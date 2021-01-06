from typing import List, Optional

from sqlalchemy.orm import Session
from .model import Mapping
from .platform import Identity


class Acl:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, mapped_id: int, identity: Identity) -> None:
        model = Mapping(id=mapped_id, identity=identity)
        self._session.add(model)
        self._session.flush()

    def get_id(self, identity: Identity) -> Optional[int]:
        mapping = self._session.query(Mapping).filter_by(
            identity=identity,
        ).one_or_none()
        return mapping and mapping.id

    def get_identity(self, mapped_id: int) -> List[Identity]:
        query = self._session.query(Mapping).filter(
            Mapping.id == mapped_id,
        )
        return [mapping.identity for mapping in query]
