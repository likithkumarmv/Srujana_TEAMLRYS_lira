"""
Episode Grouping & Graph Relationship Builder for LIRA
Connects transactions, suppliers, and destination accounts into coherent investigative episodes.
"""
from typing import Dict, Any, List

def build_episode_graph(case: Dict[str, Any], transactions: List[Dict[str, Any]], supplier: Dict[str, Any] = None) -> Dict[str, Any]:
    nodes = []
    edges = []
    node_ids = set()

    # Case central node
    case_node_id = f"case_{case.get('id')}"
    nodes.append({
        "id": case_node_id,
        "label": case.get("case_ref", "Case"),
        "type": "case",
        "data": {
            "title": case.get("title"),
            "risk_score": case.get("risk_score"),
            "priority": case.get("priority")
        }
    })
    node_ids.add(case_node_id)

    # Supplier node
    if supplier:
        supplier_node_id = f"supplier_{supplier.get('id')}"
        nodes.append({
            "id": supplier_node_id,
            "label": supplier.get("display_name", "Supplier"),
            "type": "supplier",
            "data": {
                "verified": bool(supplier.get("last_independently_verified_at")),
                "phone": supplier.get("known_contact_phone")
            }
        })
        node_ids.add(supplier_node_id)
        edges.append({
            "id": f"edge_{case_node_id}_{supplier_node_id}",
            "source": case_node_id,
            "target": supplier_node_id,
            "label": "primary_vendor"
        })

    for idx, tx in enumerate(transactions):
        tx_node_id = f"tx_{tx.get('id')}"
        if tx_node_id not in node_ids:
            nodes.append({
                "id": tx_node_id,
                "label": f"₹{float(tx.get('amount', 0)):,.0f}",
                "type": "transaction",
                "data": {
                    "direction": tx.get("direction"),
                    "external_id": tx.get("external_id"),
                    "occurred_at": str(tx.get("occurred_at")),
                    "route": tx.get("contact_route")
                }
            })
            node_ids.add(tx_node_id)
            edges.append({
                "id": f"edge_case_tx_{idx}",
                "source": case_node_id,
                "target": tx_node_id,
                "label": "evidence_item"
            })

        # Beneficiary node
        beneficiary_fp = tx.get("beneficiary_fingerprint")
        if beneficiary_fp:
            ben_node_id = f"ben_{beneficiary_fp}"
            if ben_node_id not in node_ids:
                nodes.append({
                    "id": ben_node_id,
                    "label": beneficiary_fp,
                    "type": "beneficiary",
                    "data": {
                        "fingerprint": beneficiary_fp,
                        "is_changed": True if supplier and supplier.get("previous_beneficiary_fingerprint") != beneficiary_fp else False
                    }
                })
                node_ids.add(ben_node_id)
            edges.append({
                "id": f"edge_tx_ben_{idx}",
                "source": tx_node_id,
                "target": ben_node_id,
                "label": "directed_to"
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": f"Episode links {len(transactions)} transaction(s) with {len(nodes)} distinct graph entities."
    }
