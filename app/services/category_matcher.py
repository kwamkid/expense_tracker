import re
from app.models import Category


class CategoryMatcher:
    def __init__(self, user_id):
        self.user_id = user_id
        self.categories = Category.query.filter_by(user_id=user_id).all()

    def match_category(self, description, transaction_type):
        """Match transaction description to category"""
        if not description:
            return None

        description = description.lower()
        matched_category = None
        max_score = 0

        for category in self.categories:
            if category.type != transaction_type:
                continue

            score = self._calculate_match_score(description, category.keywords)
            if score > max_score:
                max_score = score
                matched_category = category

        return matched_category.id if matched_category else None

    def _calculate_match_score(self, description, keywords):
        """Calculate matching score based on keywords"""
        if not keywords:
            return 0

        score = 0
        keyword_list = [k.strip().lower() for k in keywords.split(',')]

        for keyword in keyword_list:
            if keyword in description:
                score += len(keyword)  # Longer matches get higher score

        return score