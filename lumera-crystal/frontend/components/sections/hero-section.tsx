"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden rounded-3xl bg-hero-glow px-6 py-20 md:px-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-3xl"
      >
        <p className="text-xs uppercase tracking-[0.24em] text-gold">LUMERA CRYSTAL</p>
        <h1 className="mt-4 font-serif text-4xl leading-tight text-ink md:text-6xl">
          在克制的光泽里，
          <br />
          找到你的能量节奏
        </h1>
        <p className="mt-6 max-w-2xl text-sm leading-7 text-ink/70 md:text-base">
          来自天然矿石的细腻光感，融合现代设计语言。为日常穿搭、情绪稳定与仪式感，提供一份柔和但坚定的支持。
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/products">
            <Button>探索精选晶石</Button>
          </Link>
          <Link href="/about" className="rounded-full border border-ink/30 px-5 py-2.5 text-sm text-ink hover:border-ink">
            了解品牌故事
          </Link>
        </div>
      </motion.div>
    </section>
  );
}
