from typing import Container, Optional, Type
from enum import Enum

from pydantic import BaseConfig, BaseModel, create_model
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


class OrmConfig(BaseConfig):
    orm_mode = True

def sqlalchemy_to_pydantic(
    db_model: Type, *, config: Type = OrmConfig, exclude: Container[str] = [],
    pydantic_model_name: str = None
) -> Type[BaseModel]:
    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if not isinstance(attr, ColumnProperty) or not attr.columns:
            continue

        name = attr.key
        if name in exclude:
            continue
        column = attr.columns[0]
        python_type: Optional[type] = None
        if hasattr(column.type, "impl") and hasattr(column.type.impl, "python_type"):
            python_type = column.type.impl.python_type
        elif hasattr(column.type, "python_type"):
            python_type = column.type.python_type
        assert python_type, f"Could not infer python_type for {column}"
        if python_type == str and type(column.type).__name__.lower() == 'enum':
            python_type = Enum(column.name, [(_, _) for _ in column.type.enums], type=str)
        default = None
        if column.default is None and not column.nullable:
            default = ...
        fields[name] = (python_type, default)
    pydantic_model = create_model(
        db_model.__name__ if not pydantic_model_name else pydantic_model_name, __config__=config, **fields  # type: ignore
    )
    return pydantic_model
