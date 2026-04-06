from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import AdminUser, Category, Post, Product


def seed_categories(session):
    data = [
        ("紫水晶", "amethyst", "安抚情绪与专注力提升", "https://images.unsplash.com/photo-1523712999610-f77fbcfc3843", 1),
        ("白水晶", "clear-quartz", "净化与能量放大", "https://images.unsplash.com/photo-1516733725897-1aa73b87c8e3", 2),
        ("粉晶", "rose-quartz", "温柔与爱意连接", "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab", 3),
        ("黄水晶", "citrine", "丰盛与自信激活", "https://images.unsplash.com/photo-1491553895911-0055eca6402d", 4),
        ("月光石", "moonstone", "直觉与柔和守护", "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee", 5),
        ("黑曜石", "obsidian", "边界与安全感", "https://images.unsplash.com/photo-1489515217757-5fd1be406fef", 6),
        ("拉长石", "labradorite", "灵感与转化", "https://images.unsplash.com/photo-1473445361085-b9a07f55608b", 7),
        ("海蓝宝", "aquamarine", "沟通与平静", "https://images.unsplash.com/photo-1482192596544-9eb780fc7f66", 8),
    ]

    for name, slug, desc, image, order in data:
        exists = session.scalar(select(Category).where(Category.slug == slug))
        if exists:
            continue
        session.add(
            Category(
                name=name,
                slug=slug,
                description=desc,
                cover_image=image,
                sort_order=order,
            )
        )
    session.commit()


def seed_products(session):
    categories = {c.slug: c for c in session.scalars(select(Category)).all()}
    sample = [
        {
            "slug": "amethyst-dawn-bracelet",
            "name": "晨雾紫水晶手链",
            "subtitle": "为高压节奏带来安静专注",
            "short_description": "精选 8mm 乌拉圭紫水晶，通勤与冥想皆宜。",
            "full_description": "这款晨雾紫水晶手链以高透度珠体与柔光金属件组合，轻盈但有存在感。适合在忙碌日程中建立稳定的内在节奏。",
            "price": Decimal("499.00"),
            "cover_image": "https://images.unsplash.com/photo-1617038220319-276d3cfab638",
            "gallery_images": [
                "https://images.unsplash.com/photo-1617038220319-276d3cfab638",
                "https://images.unsplash.com/photo-1617038220319-12d3cfab633",
            ],
            "stock": 36,
            "category_slug": "amethyst",
            "crystal_type": "Amethyst",
            "color": "紫晶调",
            "origin": "乌拉圭",
            "size": "8mm",
            "material": "天然紫水晶 / 14K 包金隔珠",
            "chakra": "眉心轮",
            "intention": "平静",
            "is_featured": True,
            "is_new": True,
        },
        {
            "slug": "rose-whisper-necklace",
            "name": "粉晶低语项链",
            "subtitle": "柔和光泽，适合日常叠戴",
            "short_description": "细链与粉晶小切面结合，轻奢不喧哗。",
            "full_description": "粉晶低语项链采用低饱和烟粉色调，和米白、灰调穿搭自然融合。适合作为礼赠与自我犒赏。",
            "price": Decimal("699.00"),
            "cover_image": "https://images.unsplash.com/photo-1611085583191-a3b181a88401",
            "gallery_images": [
                "https://images.unsplash.com/photo-1611085583191-a3b181a88401",
                "https://images.unsplash.com/photo-1611085583191-b3b181a88402",
            ],
            "stock": 21,
            "category_slug": "rose-quartz",
            "crystal_type": "Rose Quartz",
            "color": "烟粉",
            "origin": "马达加斯加",
            "size": "40cm+5cm 延长链",
            "material": "天然粉晶 / 925 银镀金",
            "chakra": "心轮",
            "intention": "爱情",
            "is_featured": True,
            "is_new": False,
        },
        {
            "slug": "obsidian-guard-ring",
            "name": "黑曜守护戒",
            "subtitle": "极简墨色，日夜皆可佩戴",
            "short_description": "低调镜面黑曜石切面，塑造有边界感的风格。",
            "full_description": "黑曜守护戒适合需要专注与界限感的人群，深墨色与金属冷调形成高级对比。",
            "price": Decimal("899.00"),
            "cover_image": "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3",
            "gallery_images": [
                "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3",
                "https://images.unsplash.com/photo-1522312346375-d1a52e2b99b4",
            ],
            "stock": 14,
            "category_slug": "obsidian",
            "crystal_type": "Obsidian",
            "color": "深墨绿",
            "origin": "墨西哥",
            "size": "可调",
            "material": "天然黑曜石 / 钛钢",
            "chakra": "海底轮",
            "intention": "守护",
            "is_featured": False,
            "is_new": True,
        },
    ]

    for item in sample:
        exists = session.scalar(select(Product).where(Product.slug == item["slug"]))
        if exists:
            continue
        category = categories[item["category_slug"]]
        session.add(
            Product(
                slug=item["slug"],
                name=item["name"],
                subtitle=item["subtitle"],
                short_description=item["short_description"],
                full_description=item["full_description"],
                price=item["price"],
                cover_image=item["cover_image"],
                gallery_images=item["gallery_images"],
                stock=item["stock"],
                category_id=category.id,
                crystal_type=item["crystal_type"],
                color=item["color"],
                origin=item["origin"],
                size=item["size"],
                material=item["material"],
                chakra=item["chakra"],
                intention=item["intention"],
                is_featured=item["is_featured"],
                is_new=item["is_new"],
                status="active",
            )
        )
    session.commit()


def seed_posts(session):
    posts = [
        {
            "slug": "how-to-choose-your-first-crystal",
            "title": "第一次选水晶，不靠玄学也能选到对的",
            "excerpt": "从颜色、佩戴场景到预算，给新手一份可执行指南。",
            "cover_image": "https://images.unsplash.com/photo-1519741497674-611481863552",
            "content": """
## 先看场景，再看寓意
通勤、会谈、休息、练习冥想，这些场景决定你需要的能量关键词。

## 克制配色更高级
浅灰、米白、深墨绿、烟粉更适合日常长期佩戴，不会显得用力过猛。

## 从一件开始
建议先从手链或项链入门，一件品质稳定的产品远好过大量冲动购买。
""",
            "author": "LUMERA 编辑部",
            "tags": ["入门", "选购", "风格"],
            "seo_title": "LUMERA CRYSTAL | 第一次选水晶指南",
            "seo_description": "新手选水晶三步法：场景、配色、预算。",
        },
        {
            "slug": "crystal-care-guide",
            "title": "宝石与水晶日常养护：让光泽保持在最佳状态",
            "excerpt": "清洁、收纳、补能的实用方法，适用于日常佩戴。",
            "cover_image": "https://images.unsplash.com/photo-1509042239860-f550ce710b93",
            "content": """
## 轻柔清洁
使用软布与清水即可，避免化学清洁剂长时间接触。

## 分区收纳
不同硬度的晶石建议分袋放置，减少摩擦损耗。

## 定期休息
不必全天候佩戴，让饰品在干燥环境中休息可延长寿命。
""",
            "author": "LUMERA 内容团队",
            "tags": ["保养", "佩戴", "指南"],
            "seo_title": "LUMERA CRYSTAL | 水晶养护指南",
            "seo_description": "日常清洁与收纳建议，保持宝石光泽。",
        },
    ]

    for p in posts:
        exists = session.scalar(select(Post).where(Post.slug == p["slug"]))
        if exists:
            continue
        session.add(
            Post(
                slug=p["slug"],
                title=p["title"],
                excerpt=p["excerpt"],
                cover_image=p["cover_image"],
                content=p["content"],
                author=p["author"],
                published_at=datetime.now(timezone.utc),
                tags=p["tags"],
                seo_title=p["seo_title"],
                seo_description=p["seo_description"],
                status="published",
            )
        )
    session.commit()


def main() -> None:
    with SessionLocal() as session:
        admin_exists = session.scalar(select(AdminUser).where(AdminUser.email == settings.admin_default_email))
        if not admin_exists:
            session.add(
                AdminUser(
                    email=settings.admin_default_email,
                    password_hash=get_password_hash(settings.admin_default_password),
                    is_active=True,
                )
            )
            session.commit()
        seed_categories(session)
        seed_products(session)
        seed_posts(session)
    print("Seed completed.")


if __name__ == "__main__":
    main()
