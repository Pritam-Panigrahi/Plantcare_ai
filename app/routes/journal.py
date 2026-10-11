import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, Response
from app.models import db, NatureDiscovery

journal_bp = Blueprint("journal", __name__)

@journal_bp.route("/journal")
def journal():
    """Nature Journal showing personal observations with filtering and search."""
    category = request.args.get("category", "all")
    search_query = request.args.get("q", "").strip()

    query = NatureDiscovery.query

    if category and category != "all":
        query = query.filter_by(category=category)

    if search_query:
        search_like = f"%{search_query}%"
        query = query.filter(
            db.or_(
                NatureDiscovery.common_name.ilike(search_like),
                NatureDiscovery.scientific_name.ilike(search_like),
                NatureDiscovery.user_notes.ilike(search_like),
                NatureDiscovery.location_name.ilike(search_like),
                NatureDiscovery.visible_characteristics.ilike(search_like),
            )
        )

    entries = query.order_by(NatureDiscovery.created_at.desc()).all()
    total_count = NatureDiscovery.query.count()

    return render_template(
        "journal.html",
        entries=entries,
        current_category=category,
        search_query=search_query,
        total_count=total_count,
    )


@journal_bp.route("/journal/<int:discovery_id>")
def discovery_detail(discovery_id):
    """View full observation details, scientific notes, and educational insights."""
    discovery = NatureDiscovery.query.get_or_404(discovery_id)
    return render_template("discovery_detail.html", discovery=discovery)


@journal_bp.route("/journal/<int:discovery_id>/edit", methods=["GET", "POST"])
def edit_discovery(discovery_id):
    """Edit observation notes, common name, or location."""
    discovery = NatureDiscovery.query.get_or_404(discovery_id)

    if request.method == "POST":
        discovery.common_name = request.form.get("common_name", discovery.common_name).strip()
        discovery.scientific_name = request.form.get("scientific_name", "").strip() or None
        discovery.location_name = request.form.get("location_name", "").strip() or None
        discovery.user_notes = request.form.get("user_notes", "").strip() or None
        
        category = request.form.get("category")
        if category in {"bird", "plant", "flower", "leaf", "insect", "unknown"}:
            discovery.category = category

        db.session.commit()
        flash("Journal observation updated successfully.", "success")
        return redirect(url_for("journal.discovery_detail", discovery_id=discovery.id))

    return render_template("discovery_edit.html", discovery=discovery)


@journal_bp.route("/journal/<int:discovery_id>/delete", methods=["POST"])
def delete_discovery(discovery_id):
    """Delete a journal observation and clean up associated image file."""
    discovery = NatureDiscovery.query.get_or_404(discovery_id)
    image_file = discovery.image_filename

    # Delete record
    db.session.delete(discovery)
    db.session.commit()

    # Safely remove image file from disk if it exists
    if image_file:
        try:
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], image_file)
            if os.path.exists(upload_path):
                os.remove(upload_path)
        except Exception:
            pass

    flash("Observation deleted from your journal.", "info")
    return redirect(url_for("journal.journal"))


@journal_bp.route("/journal/export")
def export_journal():
    """Export journal entries as formatted JSON for local backup."""
    entries = NatureDiscovery.query.order_by(NatureDiscovery.created_at.desc()).all()
    export_data = {
        "export_date": entries[0].created_at.isoformat() if entries else "",
        "total_observations": len(entries),
        "entries": [e.to_dict() for e in entries],
    }
    return jsonify(export_data)
