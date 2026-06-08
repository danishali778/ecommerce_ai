from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select

from app.repositories.base import Repository
from app.repositories.models import PriceRecommendation, PriceReferenceInput, PricingRule


class PricingRepository(Repository):
    def list_rules(self, organization_id: UUID, store_id: UUID) -> list[PricingRule]:
        query = (
            select(PricingRule)
            .where(PricingRule.organization_id == organization_id, PricingRule.store_id == store_id)
            .order_by(PricingRule.updated_at.desc())
        )
        return list(self.db.scalars(query))

    def get_rule(self, organization_id: UUID, store_id: UUID, rule_id: UUID) -> PricingRule | None:
        return self.db.scalar(
            select(PricingRule).where(
                PricingRule.organization_id == organization_id,
                PricingRule.store_id == store_id,
                PricingRule.id == rule_id,
            )
        )

    def find_rule_for_target(
        self,
        organization_id: UUID,
        store_id: UUID,
        *,
        product_id: UUID | None = None,
        variant_id: UUID | None = None,
    ) -> PricingRule | None:
        query = select(PricingRule).where(
            PricingRule.organization_id == organization_id,
            PricingRule.store_id == store_id,
            PricingRule.is_enabled.is_(True),
        )
        if variant_id:
            query = query.where(
                or_(
                    PricingRule.variant_id == variant_id,
                    PricingRule.product_id == product_id,
                )
            )
        elif product_id:
            query = query.where(PricingRule.product_id == product_id)
        query = query.order_by(PricingRule.variant_id.is_not(None).desc(), PricingRule.updated_at.desc())
        return self.db.scalar(query)

    def create_rule(self, **values) -> PricingRule:
        rule = PricingRule(**values)
        self.db.add(rule)
        self.db.flush()
        return rule

    def update_rule(self, rule: PricingRule, **values) -> PricingRule:
        for key, value in values.items():
            setattr(rule, key, value)
        self.db.flush()
        return rule

    def delete_rule(self, rule: PricingRule) -> None:
        self.db.delete(rule)
        self.db.flush()

    def create_reference_input(self, **values) -> PriceReferenceInput:
        reference_input = PriceReferenceInput(**values)
        self.db.add(reference_input)
        self.db.flush()
        return reference_input

    def get_reference_input(self, organization_id: UUID, store_id: UUID, reference_input_id: UUID) -> PriceReferenceInput | None:
        return self.db.scalar(
            select(PriceReferenceInput).where(
                PriceReferenceInput.organization_id == organization_id,
                PriceReferenceInput.store_id == store_id,
                PriceReferenceInput.id == reference_input_id,
            )
        )

    def list_reference_inputs(self, organization_id: UUID, store_id: UUID, *, import_batch_id: str | None = None) -> list[PriceReferenceInput]:
        query = (
            select(PriceReferenceInput)
            .where(PriceReferenceInput.organization_id == organization_id, PriceReferenceInput.store_id == store_id)
            .order_by(PriceReferenceInput.created_at.desc())
        )
        if import_batch_id:
            query = query.where(PriceReferenceInput.import_batch_id == import_batch_id)
        return list(self.db.scalars(query))

    def create_recommendation(self, **values) -> PriceRecommendation:
        recommendation = PriceRecommendation(**values)
        self.db.add(recommendation)
        self.db.flush()
        return recommendation

    def update_recommendation(self, recommendation: PriceRecommendation, **values) -> PriceRecommendation:
        for key, value in values.items():
            setattr(recommendation, key, value)
        self.db.flush()
        return recommendation

    def get_recommendation(self, organization_id: UUID, store_id: UUID, recommendation_id: UUID) -> PriceRecommendation | None:
        return self.db.scalar(
            select(PriceRecommendation).where(
                PriceRecommendation.organization_id == organization_id,
                PriceRecommendation.store_id == store_id,
                PriceRecommendation.id == recommendation_id,
            )
        )

    def list_recommendations(
        self,
        organization_id: UUID,
        store_id: UUID,
        *,
        status: str | None = None,
        variant_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[PriceRecommendation]:
        query = (
            select(PriceRecommendation)
            .where(PriceRecommendation.organization_id == organization_id, PriceRecommendation.store_id == store_id)
            .order_by(PriceRecommendation.created_at.desc())
        )
        if status:
            query = query.where(PriceRecommendation.status == status)
        if variant_id:
            query = query.where(PriceRecommendation.variant_id == variant_id)
        if product_id:
            query = query.where(PriceRecommendation.product_id == product_id)
        return list(self.db.scalars(query))

