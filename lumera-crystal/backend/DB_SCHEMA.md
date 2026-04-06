## alembic_version
- version_num: character varying, nullable=NO, default=None

## categories
- id: integer, nullable=NO, default=nextval('categories_id_seq'::regclass)
- name: character varying, nullable=NO, default=None
- slug: character varying, nullable=NO, default=None
- description: text, nullable=NO, default=None
- cover_image: character varying, nullable=NO, default=None
- sort_order: integer, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()

## contact_messages
- id: integer, nullable=NO, default=nextval('contact_messages_id_seq'::regclass)
- name: character varying, nullable=NO, default=None
- email: character varying, nullable=NO, default=None
- subject: character varying, nullable=NO, default=None
- message: text, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()

## conversations
- id: integer, nullable=NO, default=nextval('conversations_id_seq'::regclass)
- session_id: character varying, nullable=NO, default=None
- role: character varying, nullable=NO, default=None
- content: text, nullable=NO, default=None
- meta: text, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()

## inquiries
- id: integer, nullable=NO, default=nextval('inquiries_id_seq'::regclass)
- user_identifier: character varying, nullable=NO, default=None
- question: text, nullable=NO, default=None
- context: text, nullable=NO, default=None
- response: text, nullable=NO, default=None
- status: character varying, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()

## newsletter_subscribers
- id: integer, nullable=NO, default=nextval('newsletter_subscribers_id_seq'::regclass)
- email: character varying, nullable=NO, default=None
- source: character varying, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()

## posts
- id: integer, nullable=NO, default=nextval('posts_id_seq'::regclass)
- slug: character varying, nullable=NO, default=None
- title: character varying, nullable=NO, default=None
- excerpt: text, nullable=NO, default=None
- cover_image: character varying, nullable=NO, default=None
- content: text, nullable=NO, default=None
- author: character varying, nullable=NO, default=None
- published_at: timestamp with time zone, nullable=YES, default=None
- tags: ARRAY, nullable=NO, default=None
- seo_title: character varying, nullable=NO, default=None
- seo_description: character varying, nullable=NO, default=None
- status: character varying, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()

## products
- id: integer, nullable=NO, default=nextval('products_id_seq'::regclass)
- slug: character varying, nullable=NO, default=None
- name: character varying, nullable=NO, default=None
- subtitle: character varying, nullable=NO, default=None
- short_description: text, nullable=NO, default=None
- full_description: text, nullable=NO, default=None
- price: numeric, nullable=NO, default=None
- cover_image: character varying, nullable=NO, default=None
- gallery_images: ARRAY, nullable=NO, default=None
- stock: integer, nullable=NO, default=None
- category_id: integer, nullable=NO, default=None
- crystal_type: character varying, nullable=NO, default=None
- color: character varying, nullable=NO, default=None
- origin: character varying, nullable=NO, default=None
- size: character varying, nullable=NO, default=None
- material: character varying, nullable=NO, default=None
- chakra: character varying, nullable=NO, default=None
- intention: character varying, nullable=NO, default=None
- is_featured: boolean, nullable=NO, default=None
- is_new: boolean, nullable=NO, default=None
- status: character varying, nullable=NO, default=None
- created_at: timestamp with time zone, nullable=NO, default=now()
- updated_at: timestamp with time zone, nullable=NO, default=now()
