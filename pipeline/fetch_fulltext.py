"""Step 4: fetch open-access full text + supplements and complete §4 fields.

Full-text JATS XML and supplement archives are saved under data/fulltext/
(gitignored) and never redistributed. From the XML we fill the §4 fields that
metadata cannot give: SPDX license, conflicts of interest, funding statement
and dataset/supplement links. Absent statements get a §3 missing_reason.
"""
from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET

import requests

from common import CORPUS_FILE, EUROPE_PMC, FULLTEXT_DIR, get, read_jsonl, write_jsonl
from schema import PIPELINE_VERSION, Publication, now_utc, validate

SUPPLEMENT_DIR = FULLTEXT_DIR / "supplements"
MAX_SUPPLEMENT_BYTES = 50 * 1024 * 1024
XLINK = "{http://www.w3.org/1999/xlink}href"
COI_TYPE = re.compile(r"coi|conflict|competing", re.I)
COI_TITLE = re.compile(r"conflicts? of interest|competing interests?|declaration of "
                       r"(conflicting )?interests?|disclosures?", re.I)
DATA_TYPE = re.compile(r"data[-_ ]availability", re.I)
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def text_of(el: ET.Element, skip_title: bool = True) -> str:
    parts = []
    for child in el.iter():
        if skip_title and child.tag == "title":
            continue
        parts.append(child.text or "")
        if child is not el:
            parts.append(child.tail or "")
    return " ".join(" ".join(parts).split())


# --- license -----------------------------------------------------------------

def spdx_license(root: ET.Element) -> tuple[str | None, str | None]:
    lic = root.find(".//permissions/license")
    if lic is None:
        return None, None
    href = lic.get(XLINK) or ""
    text = text_of(lic, skip_title=False)
    hrefs = " ".join([href] + [e.get(XLINK, "") for e in lic.iter()])
    if m := re.search(r"creativecommons\.org/licenses/([a-z-]+)/(\d\.\d)", hrefs, re.I):
        return f"CC-{m.group(1).upper()}-{m.group(2)}", text[:300]
    if "publicdomain/zero" in hrefs:
        return "CC0-1.0", text[:300]
    m = re.search(r"Creative Commons (Attribution(?:[- ](?:Non-?Commercial|NoDerivs|"
                  r"NoDerivatives|ShareAlike))*)[^0-9]{0,40}(\d\.\d)?", text, re.I)
    if m:
        parts = ["BY"]
        tail = m.group(1).lower()
        if "noncommercial" in tail.replace("-", ""):
            parts.append("NC")
        if "noderiv" in tail:
            parts.append("ND")
        if "sharealike" in tail:
            parts.append("SA")
        spdx = "CC-" + "-".join(parts)
        return (f"{spdx}-{m.group(2)}" if m.group(2) else spdx), text[:300]
    if "AuthorChoice" in text:
        return "LicenseRef-ACS-AuthorChoice", text[:300]
    return "LicenseRef-publisher-open-access", text[:300]


# --- statements ----------------------------------------------------------------

def find_statement(root: ET.Element, type_re: re.Pattern, title_re: re.Pattern | None) -> str | None:
    for el in root.iter():
        if el.tag not in {"fn", "notes", "sec"}:
            continue
        kind = el.get("fn-type") or el.get("notes-type") or el.get("sec-type") or ""
        title = el.find("title")
        title_text = text_of(title, skip_title=False) if title is not None else ""
        if type_re.search(kind) or (title_re and title_re.search(title_text)):
            if body := text_of(el):
                return body[:1000]
    return None


def funding_statement(root: ET.Element) -> str | None:
    el = root.find(".//funding-group/funding-statement")
    if el is not None and (t := text_of(el)):
        return t[:1000]
    return find_statement(root, re.compile(r"funding|financial-disclosure", re.I),
                          re.compile(r"^funding|financial disclosure", re.I))


def dataset_links(root: ET.Element, pmcid: str) -> list[dict]:
    links = []
    if stmt := find_statement(root, DATA_TYPE, re.compile(r"data availability", re.I)):
        links.append({"type": "data_availability_statement", "text": stmt[:500],
                      "urls": sorted(set(URL_RE.findall(stmt)))})
    for sm in root.iter("supplementary-material"):
        hrefs = [sm.get(XLINK)] + [e.get(XLINK) for e in sm.iter() if e.get(XLINK)]
        for h in dict.fromkeys(filter(None, hrefs)):
            links.append({"type": "supplementary_file", "file": h,
                          "europe_pmc_archive": f"{EUROPE_PMC}/{pmcid}/supplementaryFiles"})
    return links


def fetch_supplements(pmcid: str) -> dict:
    path = SUPPLEMENT_DIR / f"{pmcid}.zip"
    if path.exists():
        data = path.read_bytes()
    else:
        try:
            # Some archives are built on request and can hang, so: short timeout, no retries.
            resp = get(f"{EUROPE_PMC}/{pmcid}/supplementaryFiles", timeout=25, retries=1)
        except requests.RequestException as e:
            # One slow archive must not discard the whole run; it is retried on the next run.
            return {"status": f"failed_{type(e).__name__}", "file": None}
        if resp.status_code != 200 or not resp.content.startswith(b"PK"):
            return {"status": f"none_http_{resp.status_code}", "file": None}
        if len(resp.content) > MAX_SUPPLEMENT_BYTES:
            return {"status": "skipped_too_large", "file": None, "bytes": len(resp.content)}
        data = resp.content
        SUPPLEMENT_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {"status": "ok", "file": str(path.relative_to(FULLTEXT_DIR.parent.parent)),
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(read_jsonl(CORPUS_FILE))
    ok = invalid = 0
    for row in rows:
        missing, ext = row["missing_reasons"], row["extended"]
        path = FULLTEXT_DIR / f"{row['pmcid']}.xml"
        if path.exists():
            data = path.read_bytes()
        else:
            try:
                resp = get(f"{EUROPE_PMC}/{row['pmcid']}/fullTextXML")
            except requests.RequestException as e:
                ext["fulltext"] = {"fetch_status": f"failed_{type(e).__name__}"}
                print(f"  FAIL {row['pmcid']} {type(e).__name__}")
                continue
            if resp.status_code != 200 or not resp.content.lstrip().startswith(b"<"):
                ext["fulltext"] = {"fetch_status": f"failed_http_{resp.status_code}"}
                print(f"  FAIL {row['pmcid']} http {resp.status_code}")
                continue
            data = resp.content
            path.write_bytes(data)
        root = ET.fromstring(data)
        sections = len(root.findall(".//body//sec"))

        spdx, license_text = spdx_license(root)
        # Keep a specific metadata license (e.g. CC-BY) over a vague XML one.
        if spdx and (not row["license"] or not spdx.startswith("LicenseRef-publisher")):
            row["license"] = spdx
            missing.pop("license", None)
        ext["license_text"] = license_text

        coi = find_statement(root, COI_TYPE, COI_TITLE)
        ext["conflicts_of_interest"] = coi
        if not ext["funding"] and (stmt := funding_statement(root)):
            ext["funding"] = [{"statement": stmt}]
        supplements = fetch_supplements(row["pmcid"])
        links = dataset_links(root, row["pmcid"])
        ext["dataset_links"] = links or None

        ext["fulltext"] = {
            "fetch_status": "ok" if sections else "ok_no_body_sections",
            "file": str(path.relative_to(FULLTEXT_DIR.parent.parent)),
            "sha256": hashlib.sha256(data).hexdigest(),
            "format": "JATS XML",
            "body_sections": sections,
            "retrieved_at": now_utc(),
            "supplements": supplements,
        }
        row["meta"]["updated_at"] = now_utc()
        row["meta"]["pipeline_version"] = PIPELINE_VERSION
        if errs := validate(Publication, row):
            invalid += 1
            print(f"  SCHEMA {row['publication_id']}: {errs}")
        ok += 1
        print(f"  ok   {row['pmcid']:11s} {row['license'] or '-':32s} "
              f"coi={'y' if coi else 'n'} links={len(links):2d} "
              f"suppl={supplements['status']:10s} {row['title'][:40]}")
    write_jsonl(CORPUS_FILE, rows)
    print(f"fetched {ok}/{len(rows)} full texts; schema errors: {invalid}")


if __name__ == "__main__":
    main()
