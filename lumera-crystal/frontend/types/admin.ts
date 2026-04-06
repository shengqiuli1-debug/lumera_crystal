export type AdminProductStatus = "draft" | "active" | "archived";
export type AdminPostStatus = "draft" | "published" | "archived";

export interface AdminMediaAsset {
  id: number;
  url: string;
  file_name: string;
  mime_type: string;
  media_kind: string;
  file_size: number;
  duration_seconds?: number | null;
  alt_text?: string | null;
}

export interface AdminUser {
  id: number;
  email: string;
  is_active: boolean;
  last_login_at?: string;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  admin: AdminUser;
}

export interface AdminCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  cover_image: string;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface AdminProduct {
  id: number;
  slug: string;
  name: string;
  subtitle: string;
  short_description: string;
  full_description: string;
  price: string;
  cover_media_id?: number;
  gallery_media_ids?: number[];
  cover_image: string;
  gallery_images: string[];
  cover_image_asset?: AdminMediaAsset | null;
  gallery_image_assets?: AdminMediaAsset[];
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
  status: AdminProductStatus;
  created_at: string;
  updated_at: string;
}

export interface AdminProductListResponse {
  page: number;
  page_size: number;
  total: number;
  items: AdminProduct[];
}

export interface AdminPost {
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
  status: AdminPostStatus;
  created_at: string;
  updated_at: string;
}

export interface AdminPostListResponse {
  page: number;
  page_size: number;
  total: number;
  items: AdminPost[];
}

export interface AdminMessage {
  id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  is_read: boolean;
  auto_reply_status: string;
  auto_reply_subject: string;
  auto_reply_body: string;
  auto_replied_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminMessageListResponse {
  page: number;
  page_size: number;
  total: number;
  items: AdminMessage[];
}

export interface AdminNewsletterItem {
  id: number;
  email: string;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface AdminNewsletterListResponse {
  page: number;
  page_size: number;
  total: number;
  items: AdminNewsletterItem[];
}

export interface DashboardStat {
  label: string;
  value: number;
}

export interface DashboardRecentProduct {
  id: number;
  name: string;
  status: string;
  updated_at: string;
}

export interface DashboardLatestMessage {
  id: number;
  name: string;
  subject: string;
  is_read: boolean;
  created_at: string;
}

export interface DashboardOverviewResponse {
  stats: DashboardStat[];
  recent_products: DashboardRecentProduct[];
  latest_messages: DashboardLatestMessage[];
}
