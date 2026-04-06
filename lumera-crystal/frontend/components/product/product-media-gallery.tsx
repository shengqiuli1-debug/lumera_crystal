"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Expand, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { MediaAsset } from "@/types";

type MediaType = "image" | "video";

type MediaItem = {
  url: string;
  alt: string;
  type: MediaType;
};

function isVideoUrl(url: string) {
  return /\.(mp4|webm|mov)$/i.test(url);
}

function resolveMediaType(url: string, asset?: MediaAsset): MediaType {
  if (asset?.media_kind === "video") return "video";
  return isVideoUrl(url) ? "video" : "image";
}

export function ProductMediaGallery({
  name,
  coverImage,
  coverAsset,
  galleryImages,
  galleryAssets,
}: {
  name: string;
  coverImage: string;
  coverAsset?: MediaAsset | null;
  galleryImages: string[];
  galleryAssets?: MediaAsset[];
}) {
  const items = useMemo<MediaItem[]>(() => {
    const media: MediaItem[] = [];
    if (coverImage) {
      media.push({
        url: coverImage,
        alt: `${name} 封面`,
        type: resolveMediaType(coverImage, coverAsset || undefined),
      });
    }
    galleryImages.forEach((url, index) => {
      if (!url) return;
      media.push({
        url,
        alt: `${name} 图集 ${index + 1}`,
        type: resolveMediaType(url, galleryAssets?.[index]),
      });
    });
    return media;
  }, [coverAsset, coverImage, galleryAssets, galleryImages, name]);

  const [activeIndex, setActiveIndex] = useState(0);
  const [viewerIndex, setViewerIndex] = useState<number | null>(null);

  const activeItem = items[activeIndex];
  const viewerItem = viewerIndex === null ? null : items[viewerIndex];

  useEffect(() => {
    if (activeIndex >= items.length) setActiveIndex(0);
  }, [activeIndex, items.length]);

  useEffect(() => {
    if (viewerIndex === null) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setViewerIndex(null);
      if (event.key === "ArrowLeft") {
        setViewerIndex((prev) => {
          if (prev === null) return prev;
          return (prev - 1 + items.length) % items.length;
        });
      }
      if (event.key === "ArrowRight") {
        setViewerIndex((prev) => {
          if (prev === null) return prev;
          return (prev + 1) % items.length;
        });
      }
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [items.length, viewerIndex]);

  if (!activeItem) return null;

  return (
    <>
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => setViewerIndex(activeIndex)}
          className="group relative block h-[460px] w-full overflow-hidden rounded-3xl border border-mist/70 text-left"
        >
          {activeItem.type === "video" ? (
            <video src={activeItem.url} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.015]" controls muted playsInline />
          ) : (
            <img src={activeItem.url} alt={activeItem.alt} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.015]" />
          )}
          <div className="pointer-events-none absolute right-3 top-3 inline-flex items-center gap-1 rounded-full border border-white/50 bg-black/25 px-2.5 py-1 text-xs text-white backdrop-blur">
            <Expand className="h-3.5 w-3.5" />
            查看大图
          </div>
        </button>

        {items.length > 1 ? (
          <div className="grid grid-cols-4 gap-3 md:grid-cols-5">
            {items.map((item, index) => {
              const active = index === activeIndex;
              return (
                <button
                  key={`${item.url}-${index}`}
                  type="button"
                  onClick={() => setActiveIndex(index)}
                  className={`relative h-24 overflow-hidden rounded-2xl border transition ${active ? "border-ink/70 ring-2 ring-ink/20" : "border-mist/70 hover:border-mist"}`}
                >
                  {item.type === "video" ? (
                    <video src={item.url} className="h-full w-full object-cover" muted playsInline />
                  ) : (
                    <img src={item.url} alt={item.alt} className="h-full w-full object-cover" />
                  )}
                </button>
              );
            })}
          </div>
        ) : null}
      </div>

      <AnimatePresence>
        {viewerItem ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md"
            onClick={() => setViewerIndex(null)}
          >
            <div className="relative flex h-full w-full items-center justify-center px-4 py-8">
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  setViewerIndex(null);
                }}
                className="absolute right-5 top-5 inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/25 bg-black/40 text-white transition hover:bg-black/60"
              >
                <X className="h-5 w-5" />
              </button>

              {items.length > 1 ? (
                <>
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      setViewerIndex((viewerIndex! - 1 + items.length) % items.length);
                    }}
                    className="absolute left-5 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/25 bg-black/40 text-white transition hover:bg-black/60"
                  >
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      setViewerIndex((viewerIndex! + 1) % items.length);
                    }}
                    className="absolute right-5 top-1/2 inline-flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full border border-white/25 bg-black/40 text-white transition hover:bg-black/60"
                  >
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </>
              ) : null}

              <motion.div
                key={`${viewerItem.url}-${viewerIndex}`}
                initial={{ opacity: 0, y: 8, scale: 0.985 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.985 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
                className="max-h-[86vh] max-w-[92vw] overflow-hidden rounded-3xl border border-white/20 bg-black/35 p-2 shadow-2xl"
                onClick={(event) => event.stopPropagation()}
              >
                {viewerItem.type === "video" ? (
                  <video src={viewerItem.url} className="max-h-[82vh] max-w-[90vw] rounded-2xl object-contain" controls autoPlay muted loop playsInline />
                ) : (
                  <img src={viewerItem.url} alt={viewerItem.alt} className="max-h-[82vh] max-w-[90vw] rounded-2xl object-contain" />
                )}
              </motion.div>

              <div className="absolute bottom-5 left-1/2 -translate-x-1/2 rounded-full border border-white/20 bg-black/45 px-3 py-1 text-xs text-white/90">
                {viewerIndex! + 1} / {items.length}
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
