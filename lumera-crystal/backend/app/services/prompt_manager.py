class PromptManager:
    """Prompt template registry placeholder."""

    templates = {
        "gem_recommendation": "[TODO] 根据用户需求推荐宝石",
        "content_generation": "[TODO] 生成品牌文案与内容",
    }

    def get(self, key: str) -> str:
        return self.templates.get(key, "")
