"""SQLAlchemy repository and unit of work for the M2 article catalog."""

import json
from datetime import UTC, datetime
from types import TracebackType
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from ebauteilefuchs.domain.articles import (
    Article,
    ArticleAttribute,
    AttributeDefinition,
    Category,
    CategoryAttribute,
    Manufacturer,
    Supplier,
    SupplierPart,
)
from ebauteilefuchs.domain.errors import DuplicateReferenceError
from ebauteilefuchs.persistence.models import (
    ArticleAttributeModel,
    ArticleModel,
    AttributeDefinitionModel,
    CategoryAttributeModel,
    CategoryModel,
    ManufacturerModel,
    SupplierModel,
    SupplierPartModel,
)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _manufacturer(model: ManufacturerModel) -> Manufacturer:
    return Manufacturer(
        id=UUID(model.id),
        name=model.name,
        normalized_name=model.normalized_name,
        is_active=model.is_active,
        created_at=_aware(model.created_at),
        updated_at=_aware(model.updated_at),
    )


def _category(model: CategoryModel) -> Category:
    return Category(
        id=UUID(model.id),
        code=model.code,
        name=model.name,
        description=model.description,
        is_system=model.is_system,
        is_active=model.is_active,
        sort_order=model.sort_order,
    )


def _supplier(model: SupplierModel) -> Supplier:
    return Supplier(
        id=UUID(model.id),
        code=model.code,
        name=model.name,
        adapter_name=model.adapter_name,
        is_system=model.is_system,
        is_active=model.is_active,
    )


def _definition(model: AttributeDefinitionModel) -> AttributeDefinition:
    return AttributeDefinition(
        id=UUID(model.id),
        code=model.code,
        name=model.name,
        value_kind=model.value_kind,  # type: ignore[arg-type]
        canonical_unit=model.canonical_unit,
        is_system=model.is_system,
        is_active=model.is_active,
    )


def _article(model: ArticleModel) -> Article:
    return Article(
        id=UUID(model.id),
        name=model.name,
        manufacturer_id=UUID(model.manufacturer_id) if model.manufacturer_id else None,
        manufacturer_part_number=model.manufacturer_part_number,
        normalized_manufacturer_part_number=model.normalized_manufacturer_part_number,
        category_id=UUID(model.category_id),
        description=model.description,
        datasheet_url=model.datasheet_url,
        product_url=model.product_url,
        note=model.note,
        search_text=model.search_text,
        is_active=model.is_active,
        created_at=_aware(model.created_at),
        updated_at=_aware(model.updated_at),
    )


class SqlAlchemyArticleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_manufacturers(
        self, *, include_inactive: bool = False
    ) -> list[Manufacturer]:
        statement = select(ManufacturerModel)
        if not include_inactive:
            statement = statement.where(ManufacturerModel.is_active.is_(True))
        statement = statement.order_by(ManufacturerModel.normalized_name)
        return [_manufacturer(item) for item in self._session.scalars(statement).all()]

    def get_manufacturer(self, manufacturer_id: UUID) -> Manufacturer | None:
        model = self._session.get(ManufacturerModel, str(manufacturer_id))
        return _manufacturer(model) if model else None

    def get_manufacturer_by_normalized(
        self, normalized_name: str
    ) -> Manufacturer | None:
        model = self._session.scalar(
            select(ManufacturerModel).where(
                ManufacturerModel.normalized_name == normalized_name
            )
        )
        return _manufacturer(model) if model else None

    def add_manufacturer(self, manufacturer: Manufacturer) -> None:
        self._session.add(
            ManufacturerModel(
                id=str(manufacturer.id),
                name=manufacturer.name,
                normalized_name=manufacturer.normalized_name,
                is_active=manufacturer.is_active,
                created_at=manufacturer.created_at,
                updated_at=manufacturer.updated_at,
            )
        )

    def update_manufacturer(self, manufacturer: Manufacturer) -> None:
        model = self._session.get(ManufacturerModel, str(manufacturer.id))
        if model:
            model.name = manufacturer.name
            model.normalized_name = manufacturer.normalized_name
            model.is_active = manufacturer.is_active
            model.updated_at = manufacturer.updated_at

    def list_categories(self, *, include_inactive: bool = False) -> list[Category]:
        statement = select(CategoryModel)
        if not include_inactive:
            statement = statement.where(CategoryModel.is_active.is_(True))
        statement = statement.order_by(CategoryModel.sort_order, CategoryModel.name)
        return [_category(item) for item in self._session.scalars(statement).all()]

    def get_category(self, category_id: UUID) -> Category | None:
        model = self._session.get(CategoryModel, str(category_id))
        return _category(model) if model else None

    def add_category(self, category: Category) -> None:
        self._session.add(
            CategoryModel(
                id=str(category.id),
                code=category.code,
                name=category.name,
                description=category.description,
                is_system=category.is_system,
                is_active=category.is_active,
                sort_order=category.sort_order,
            )
        )

    def update_category(self, category: Category) -> None:
        model = self._session.get(CategoryModel, str(category.id))
        if model:
            model.name = category.name
            model.description = category.description
            model.is_active = category.is_active
            model.sort_order = category.sort_order

    def list_category_attributes(self, category_id: UUID) -> list[CategoryAttribute]:
        statement = (
            select(CategoryAttributeModel, AttributeDefinitionModel)
            .join(
                AttributeDefinitionModel,
                AttributeDefinitionModel.id
                == CategoryAttributeModel.attribute_definition_id,
            )
            .where(
                CategoryAttributeModel.category_id == str(category_id),
                AttributeDefinitionModel.is_active.is_(True),
            )
            .order_by(CategoryAttributeModel.sort_order)
        )
        return [
            CategoryAttribute(
                category_id=category_id,
                definition=_definition(definition),
                sort_order=mapping.sort_order,
                is_typical=mapping.is_typical,
                allowed_units=tuple(json.loads(mapping.allowed_units_json)),
            )
            for mapping, definition in self._session.execute(statement).all()
        ]

    def get_attribute_definition(
        self, definition_id: UUID
    ) -> AttributeDefinition | None:
        model = self._session.get(AttributeDefinitionModel, str(definition_id))
        return _definition(model) if model else None

    def list_suppliers(self, *, include_inactive: bool = False) -> list[Supplier]:
        statement = select(SupplierModel)
        if not include_inactive:
            statement = statement.where(SupplierModel.is_active.is_(True))
        statement = statement.order_by(SupplierModel.name)
        return [_supplier(item) for item in self._session.scalars(statement).all()]

    def get_supplier(self, supplier_id: UUID) -> Supplier | None:
        model = self._session.get(SupplierModel, str(supplier_id))
        return _supplier(model) if model else None

    def list_articles(self, *, include_inactive: bool = True) -> list[Article]:
        statement = select(ArticleModel)
        if not include_inactive:
            statement = statement.where(ArticleModel.is_active.is_(True))
        statement = statement.order_by(ArticleModel.name)
        return [_article(item) for item in self._session.scalars(statement).all()]

    def search_articles(
        self, tokens: tuple[str, ...], *, include_inactive: bool = False
    ) -> list[Article]:
        statement = select(ArticleModel)
        if tokens:
            statement = statement.where(
                and_(*(ArticleModel.search_text.contains(token) for token in tokens))
            )
        if not include_inactive:
            statement = statement.where(ArticleModel.is_active.is_(True))
        statement = statement.order_by(ArticleModel.name).limit(250)
        return [_article(item) for item in self._session.scalars(statement).all()]

    def get_article(self, article_id: UUID) -> Article | None:
        model = self._session.get(ArticleModel, str(article_id))
        return _article(model) if model else None

    def add_article(self, article: Article) -> None:
        # Persist a newly resolved manufacturer before the article FK is inserted.
        self._session.flush()
        self._session.add(self._article_model(article))
        # Child properties and supplier identifiers are written immediately after.
        self._session.flush()

    def update_article(self, article: Article) -> None:
        model = self._session.get(ArticleModel, str(article.id))
        if model is None:
            return
        values = self._article_model(article)
        for field in (
            "name",
            "manufacturer_id",
            "manufacturer_part_number",
            "normalized_manufacturer_part_number",
            "category_id",
            "description",
            "datasheet_url",
            "product_url",
            "note",
            "search_text",
            "is_active",
            "updated_at",
        ):
            setattr(model, field, getattr(values, field))

    @staticmethod
    def _article_model(article: Article) -> ArticleModel:
        return ArticleModel(
            id=str(article.id),
            name=article.name,
            manufacturer_id=str(article.manufacturer_id)
            if article.manufacturer_id
            else None,
            manufacturer_part_number=article.manufacturer_part_number,
            normalized_manufacturer_part_number=article.normalized_manufacturer_part_number,
            category_id=str(article.category_id),
            description=article.description,
            datasheet_url=article.datasheet_url,
            product_url=article.product_url,
            note=article.note,
            search_text=article.search_text,
            is_active=article.is_active,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    def list_article_attributes(self, article_id: UUID) -> list[ArticleAttribute]:
        statement = (
            select(ArticleAttributeModel, AttributeDefinitionModel.name)
            .outerjoin(
                AttributeDefinitionModel,
                AttributeDefinitionModel.id
                == ArticleAttributeModel.attribute_definition_id,
            )
            .where(ArticleAttributeModel.article_id == str(article_id))
            .order_by(ArticleAttributeModel.sort_order)
        )
        return [
            ArticleAttribute(
                id=UUID(model.id),
                article_id=article_id,
                attribute_definition_id=(
                    UUID(model.attribute_definition_id)
                    if model.attribute_definition_id
                    else None
                ),
                custom_name=model.custom_name,
                raw_value=model.raw_value,
                normalized_text=model.normalized_text,
                numeric_value=model.numeric_value,
                unit=model.unit,
                canonical_numeric_value=model.canonical_numeric_value,
                canonical_unit=model.canonical_unit,
                sort_order=model.sort_order,
                definition_name=definition_name,
            )
            for model, definition_name in self._session.execute(statement).all()
        ]

    def replace_article_attributes(
        self, article_id: UUID, values: list[ArticleAttribute]
    ) -> None:
        self._session.execute(
            delete(ArticleAttributeModel).where(
                ArticleAttributeModel.article_id == str(article_id)
            )
        )
        self._session.add_all(
            ArticleAttributeModel(
                id=str(value.id),
                article_id=str(article_id),
                attribute_definition_id=(
                    str(value.attribute_definition_id)
                    if value.attribute_definition_id
                    else None
                ),
                custom_name=value.custom_name,
                raw_value=value.raw_value,
                normalized_text=value.normalized_text,
                numeric_value=value.numeric_value,
                unit=value.unit,
                canonical_numeric_value=value.canonical_numeric_value,
                canonical_unit=value.canonical_unit,
                sort_order=value.sort_order,
            )
            for value in values
        )

    def list_supplier_parts(self, article_id: UUID) -> list[SupplierPart]:
        statement = (
            select(SupplierPartModel, SupplierModel.name)
            .join(SupplierModel, SupplierModel.id == SupplierPartModel.supplier_id)
            .where(SupplierPartModel.article_id == str(article_id))
            .order_by(SupplierModel.name, SupplierPartModel.supplier_part_number)
        )
        return [
            SupplierPart(
                id=UUID(model.id),
                article_id=article_id,
                supplier_id=UUID(model.supplier_id),
                supplier_part_number=model.supplier_part_number,
                normalized_supplier_part_number=model.normalized_supplier_part_number,
                product_url=model.product_url,
                created_at=_aware(model.created_at),
                updated_at=_aware(model.updated_at),
                supplier_name=supplier_name,
            )
            for model, supplier_name in self._session.execute(statement).all()
        ]

    def replace_supplier_parts(
        self, article_id: UUID, values: list[SupplierPart]
    ) -> None:
        self._session.execute(
            delete(SupplierPartModel).where(
                SupplierPartModel.article_id == str(article_id)
            )
        )
        self._session.add_all(
            SupplierPartModel(
                id=str(value.id),
                article_id=str(article_id),
                supplier_id=str(value.supplier_id),
                supplier_part_number=value.supplier_part_number,
                normalized_supplier_part_number=value.normalized_supplier_part_number,
                product_url=value.product_url,
                created_at=value.created_at,
                updated_at=value.updated_at,
            )
            for value in values
        )

    def find_supplier_part(
        self,
        supplier_id: UUID,
        normalized_number: str,
        *,
        exclude_article_id: UUID | None = None,
    ) -> Article | None:
        statement = (
            select(ArticleModel)
            .join(SupplierPartModel, SupplierPartModel.article_id == ArticleModel.id)
            .where(
                SupplierPartModel.supplier_id == str(supplier_id),
                SupplierPartModel.normalized_supplier_part_number == normalized_number,
            )
        )
        if exclude_article_id:
            statement = statement.where(ArticleModel.id != str(exclude_article_id))
        model = self._session.scalar(statement)
        return _article(model) if model else None

    def find_exact_manufacturer_part(
        self,
        manufacturer_name: str,
        part_number: str,
        *,
        exclude_article_id: UUID | None = None,
    ) -> list[Article]:
        statement = (
            select(ArticleModel)
            .join(
                ManufacturerModel, ManufacturerModel.id == ArticleModel.manufacturer_id
            )
            .where(
                ManufacturerModel.name == manufacturer_name,
                ArticleModel.manufacturer_part_number == part_number,
            )
        )
        if exclude_article_id:
            statement = statement.where(ArticleModel.id != str(exclude_article_id))
        return [_article(item) for item in self._session.scalars(statement).all()]

    def find_normalized_manufacturer_part(
        self,
        normalized_manufacturer: str,
        normalized_part_number: str,
        *,
        exclude_article_id: UUID | None = None,
    ) -> list[Article]:
        statement = (
            select(ArticleModel)
            .join(
                ManufacturerModel, ManufacturerModel.id == ArticleModel.manufacturer_id
            )
            .where(
                ManufacturerModel.normalized_name == normalized_manufacturer,
                ArticleModel.normalized_manufacturer_part_number
                == normalized_part_number,
            )
        )
        if exclude_article_id:
            statement = statement.where(ArticleModel.id != str(exclude_article_id))
        return [_article(item) for item in self._session.scalars(statement).all()]


class SqlAlchemyArticleUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.articles: SqlAlchemyArticleRepository

    def __enter__(self) -> "SqlAlchemyArticleUnitOfWork":
        self._session = self._session_factory()
        self.articles = SqlAlchemyArticleRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        if exc_type is not None:
            self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("Die Unit of Work wurde nicht geöffnet.")
        try:
            self._session.commit()
        except IntegrityError as error:
            self._session.rollback()
            raise DuplicateReferenceError(
                "Hersteller-, Artikel- oder Lieferantennummer ist bereits vorhanden."
            ) from error
