from app.repositories.admin_dashboard_repository import AdminDashboardRepository
from app.schemas.admin_dashboard import (
    DashboardLatestMessage,
    DashboardOverviewResponse,
    DashboardRecentProduct,
    DashboardStatItem,
)


class AdminDashboardService:
    def __init__(self, repo: AdminDashboardRepository) -> None:
        self.repo = repo

    def get_overview(self) -> DashboardOverviewResponse:
        counts = self.repo.counts()
        stats = [
            DashboardStatItem(label="商品总数", value=counts["products_total"]),
            DashboardStatItem(label="已上架商品", value=counts["products_active"]),
            DashboardStatItem(label="草稿商品", value=counts["products_draft"]),
            DashboardStatItem(label="分类数", value=counts["categories_total"]),
            DashboardStatItem(label="已发布博客", value=counts["posts_published"]),
        ]

        recent_products = [
            DashboardRecentProduct(
                id=item.id,
                name=item.name,
                status=item.status,
                updated_at=item.updated_at,
            )
            for item in self.repo.recent_products()
        ]
        latest_messages = [
            DashboardLatestMessage(
                id=item.id,
                name=item.name,
                subject=item.subject,
                is_read=item.is_read,
                created_at=item.created_at,
            )
            for item in self.repo.latest_messages()
        ]
        return DashboardOverviewResponse(stats=stats, recent_products=recent_products, latest_messages=latest_messages)
