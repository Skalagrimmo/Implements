from .scene_structure import STYLE_BY_BIOME

def validate_structural_grammar(world):
    errors=[]
    seen={}
    for s in world.get("sectors",[]):
        scene=s.get("scene",{})
        meta=scene.get("structural_grammar")
        pos=(s.get("sx"),s.get("sy"))
        if not isinstance(meta,dict):
            errors.append(f"sector {pos} missing structural_grammar")
            continue

        biome=s.get("biome")
        expected=STYLE_BY_BIOME.get(biome)
        if not expected:
            errors.append(f"sector {pos} unknown biome structural style {biome!r}")
            continue
        if meta.get("grammar_id") != expected["id"]:
            errors.append(f"sector {pos} grammar id disagrees with biome")
        if meta.get("path_visual") != expected["path_visual"]:
            errors.append(f"sector {pos} path visual disagrees with biome")

        variant=meta.get("variant",{})
        scene_geo=scene.get("geography",{})
        if scene_geo:
            if not variant.get("variant_id"):
                errors.append(f"sector {pos} missing subbiome structural variant id")
            if variant.get("subbiome") != scene_geo.get("subbiome"):
                errors.append(f"sector {pos} structural subbiome disagrees with geography")
            if variant.get("zone") != scene_geo.get("zone"):
                errors.append(f"sector {pos} structural zone disagrees with geography")

            declared_edges=sorted(
                e.get("edge")
                for e in scene_geo.get("transition_edges",[])
                if e.get("edge")
            )
            adapter_edges=sorted(
                e.get("edge")
                for e in meta.get("ecotone_adapters",[])
                if e.get("edge")
            )
            if declared_edges != adapter_edges:
                errors.append(f"sector {pos} ecotone adapters disagree with geography transitions")

        metrics=meta.get("metrics",{})
        if metrics.get("path_cells",0) < 8:
            errors.append(f"sector {pos} structural network too small")
        if metrics.get("components") != 1:
            errors.append(f"sector {pos} structural network is disconnected")

        seen.setdefault(biome,set()).add(meta.get("grammar_id"))

    return errors
