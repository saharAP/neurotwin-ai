import type { Metadata } from "next";
import Link from "next/link";
import { isFixture } from "@/lib/data";
import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroTwin Neuron Outcome Atlas",
  description: "Source-linked, AI-extracted evidence on how substances and environmental settings change neurons: neurogenesis, spinogenesis, dendritogenesis, plasticity and neurodegeneration (MVP v0).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <div className="wrap">
            <Link href="/" className="brand">NeuroTwin · Neuron Outcome Atlas</Link>
            <nav className="nav">
              <Link href="/">Atlas</Link>
              <Link href="/studies">Studies</Link>
              <Link href="/about">About the data</Link>
            </nav>
          </div>
        </header>
        {isFixture && (
          <div className="notice fixture">
            <div className="wrap">TEST FIXTURE: these measurements are made up for UI testing and are not real evidence.</div>
          </div>
        )}
        <div className="notice">
          <div className="wrap">
            Research use only · AI-extracted, not expert-reviewed · Check every value against its source quote
          </div>
        </div>
        <main className="wrap">{children}</main>
      </body>
    </html>
  );
}
