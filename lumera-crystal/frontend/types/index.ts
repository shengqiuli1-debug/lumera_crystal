export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  cover_image: string;
  sort_order: number;
}

export interface MediaAsset {
  id: number;
  url: string;
  file_name: string;
  mime_type: string;
  media_kind: string;
  file_size: number;
  duration_seconds?: number | null;
}

export interface Product {
  id: number;
  slug: string;
  name: string;
  subtitle: string;
  short_description: string;
  full_description: string;
  price: string;
  cover_image: string;
  gallery_images: string[];
  cover_image_asset?: MediaAsset | null;
  gallery_image_assets?: MediaAsset[];
  stock: number;
  category_id: number;
  crystal_type: string;
  color: string;
  origin: string;
  size: string;
  material: string;
  chakra: string;
  intention: string;
  is_featured: boolean;
  is_new: boolean;
  status: string;
}

export interface ProductListResponse {
  page: number;
  page_size: number;
  total: number;
  items: Product[];
}

export interface Post {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  cover_image: string;
  content: string;
  author: string;
  published_at?: string;
  tags: string[];
  seo_title: string;
  seo_description: string;
  status: string;
}

export interface PostListResponse {
  page: number;
  page_size: number;
  total: number;
  items: Post[];
}
