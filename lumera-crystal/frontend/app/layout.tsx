import type { Metadata } from "next";

import { RootShell } from "@/components/layout/root-shell";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://lumeracrystal.com"),
  title: {
    default: "LUMERA CRYSTAL | 现代轻奢宝石与水晶",
    template: "%s | LUMERA CRYSTAL"
  },
  description: "LUMERA CRYSTAL 提供天然宝石与水晶饰品，以现代、安静、治愈、轻奢的品牌审美服务日常生活。",
  openGraph: {
    title: "LUMERA CRYSTAL",
    description: "天然晶石与现代设计融合的品牌网站",
    type: "website",
    locale: "zh_CN"
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body><RootShell>{children}</RootShell></body>
    </html>
  );
}
