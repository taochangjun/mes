from dataclasses import dataclass

from sqlalchemy.orm import Session, joinedload

from ...models import ProcessRoute, ProcessRouteStep, Product


@dataclass
class SopChunk:
    id: str
    station_code: str
    station_name: str
    product_name: str
    chunk_type: str  # sop | safety
    text: str


def load_sop_chunks(db: Session) -> list[SopChunk]:
    """从工艺路线加载 SOP 文本块（每工位：作业步骤 + 安全注意事项）。"""
    steps = (
        db.query(ProcessRouteStep)
        .options(
            joinedload(ProcessRouteStep.station),
            joinedload(ProcessRouteStep.route).joinedload(ProcessRoute.product),
        )
        .join(ProcessRoute)
        .filter(ProcessRoute.is_active.is_(True))
        .order_by(ProcessRoute.product_id, ProcessRouteStep.sequence)
        .all()
    )

    chunks: list[SopChunk] = []
    for step in steps:
        station = step.station
        product: Product = step.route.product
        base_id = f"{product.code}-{station.code}"

        chunks.append(
            SopChunk(
                id=f"{base_id}-sop",
                station_code=station.code,
                station_name=station.name,
                product_name=product.name,
                chunk_type="sop",
                text=step.sop_content.strip(),
            )
        )
        if step.safety_notes:
            chunks.append(
                SopChunk(
                    id=f"{base_id}-safety",
                    station_code=station.code,
                    station_name=station.name,
                    product_name=product.name,
                    chunk_type="safety",
                    text=step.safety_notes.strip(),
                )
            )
    return chunks
