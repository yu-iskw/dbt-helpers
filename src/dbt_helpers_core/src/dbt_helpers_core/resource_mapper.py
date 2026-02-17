from dbt_helpers_sdk import CatalogRelation, DbtColumnIR, DbtResourceIR


def map_catalog_to_ir(relations: list[CatalogRelation]) -> list[DbtResourceIR]:
    """Map warehouse catalog relations to dbt Intermediate Representation (IR)."""
    ir_resources = []
    for rel in relations:
        columns = [
            DbtColumnIR(
                name=col.name,
                description=col.description,
                meta=col.metadata.get("meta", {}),
                tags=col.metadata.get("tags", []),
            )
            for col in rel.columns
        ]

        # Standardize metadata extraction
        metadata = rel.metadata.copy()
        metadata["identifier"] = rel.name
        if len(rel.namespace.parts) >= 1:
            metadata["source_name"] = rel.namespace.parts[-1]

        # Capture config and metadata
        config = rel.metadata.get("config", {}).copy()
        meta = rel.metadata.get("meta", {}).copy()
        tags = rel.metadata.get("tags", []).copy()

        # Map warehouse labels to meta (labels is the dbt/BigQuery term)
        if "labels" in rel.metadata:
            meta.update(rel.metadata["labels"])

        ir_resources.append(
            DbtResourceIR(
                name=rel.dbt_name or rel.name,
                description=rel.metadata.get("description"),
                columns=columns,
                meta=meta,
                tags=tags,
                config=config,
            )
        )
        # Tag the resource with extraction metadata
        ir_resources[-1].meta["_extraction_metadata"] = metadata

    return ir_resources
