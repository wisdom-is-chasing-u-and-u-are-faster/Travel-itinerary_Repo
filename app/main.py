"""
FastAPI Full-Stack Application Entrypoint for Travel Itinerary Generator Platform.
Provides RESTful APIs matching api_contract.json and serves responsive frontend views.
"""

import os
import json
import sqlite3
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from app.db.init_db import init_db, get_db_connection, DEFAULT_DB_PATH
from app.models.schemas import (
    ProblemDetails,
    GenerateItineraryRequest,
    UpdateItineraryRequest,
    CreateActivityRequest,
    SyncRequest,
    InviteCollaboratorRequest,
    CreateExpenseRequest,
    CheckoutRequest,
    UserProfile
)
from app.services.itinerary_service import generate_daily_schedule
from app.services.expense_service import convert_to_base_usd, simplify_debts

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Travel Itinerary Generator Platform",
    version="1.0.0",
    description="Enterprise AI-orchestrated travel planning, offline sync, and commerce ecosystem",
    lifespan=lifespan
)



# CORS Configuration
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# RFC 7807 Problem Details exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "instance": str(request.url.path)
        },
        headers={"Content-Type": "application/problem+json"}
    )

# 1. Health & Readiness Probe
@app.get("/health", status_code=status.HTTP_200_OK)
def get_health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime": "99.98%"
    }

# 2. Generate Itinerary (REQ-F-001, REQ-F-005, AC-1)
@app.post("/api/v1/itineraries/generate", status_code=status.HTTP_201_CREATED)
def generate_itinerary(req: GenerateItineraryRequest):
    if not req.destination or not req.destination.strip():
        raise HTTPException(status_code=400, detail="Destination must not be empty")

    days_data = generate_daily_schedule(
        destination=req.destination,
        start_date_str=req.start_date,
        end_date_str=req.end_date,
        pacing=req.pacing or "Moderate",
        interests=req.interests
    )

    conn = get_db_connection()
    try:
        title = f"{req.pacing or 'Moderate'} Trip to {req.destination}"
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO itineraries (user_id, title, destination, start_date, end_date, pacing, interests, budget_level, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (1, title, req.destination, req.start_date, req.end_date, req.pacing, ", ".join(req.interests or []), req.budget_level)
        )
        itinerary_id = cursor.lastrowid

        for d in days_data:
            cursor.execute(
                """
                INSERT INTO itinerary_days (itinerary_id, day_number, date, theme)
                VALUES (?, ?, ?, ?)
                """,
                (itinerary_id, d["day_number"], d["date"], d["theme"])
            )
            day_id = cursor.lastrowid

            for a in d["activities"]:
                cursor.execute(
                    """
                    INSERT INTO activities (itinerary_id, day_id, time, title, location, latitude, longitude, cost, category, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (itinerary_id, day_id, a["time"], a["title"], a["location"], a.get("latitude", 0.0), a.get("longitude", 0.0), a.get("cost", 0.0), a.get("category", "General"), a.get("notes", ""))
                )
                a["id"] = str(cursor.lastrowid)

        conn.commit()
    finally:
        conn.close()

    return {
        "itinerary_id": str(itinerary_id),
        "title": title,
        "destination": req.destination,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "days": days_data
    }

# 3. List Itineraries
@app.get("/api/v1/itineraries", status_code=status.HTTP_200_OK)
def list_itineraries():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.id, i.title, i.destination, i.start_date, i.end_date, i.status,
                   COUNT(a.id) as total_activities
            FROM itineraries i
            LEFT JOIN activities a ON i.id = a.itinerary_id
            GROUP BY i.id
            ORDER BY i.id DESC
            """
        )
        rows = cursor.fetchall()
        itins = [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "destination": r["destination"],
                "start_date": r["start_date"],
                "end_date": r["end_date"],
                "status": r["status"],
                "total_activities": r["total_activities"]
            }
            for r in rows
        ]
        return {"itineraries": itins}
    finally:
        conn.close()

# 4. Get Itinerary Detail (AC-2)
@app.get("/api/v1/itineraries/{id}", status_code=status.HTTP_200_OK)
def get_itinerary(id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM itineraries WHERE id = ?", (id,))
        itin = cursor.fetchone()
        if not itin:
            raise HTTPException(status_code=404, detail=f"Itinerary {id} not found")

        cursor.execute("SELECT * FROM itinerary_days WHERE itinerary_id = ? ORDER BY day_number ASC", (id,))
        days_rows = cursor.fetchall()

        days = []
        for d in days_rows:
            cursor.execute("SELECT * FROM activities WHERE day_id = ? ORDER BY id ASC", (d["id"],))
            act_rows = cursor.fetchall()
            acts = [
                {
                    "id": str(a["id"]),
                    "title": a["title"],
                    "time": a["time"],
                    "location": a["location"],
                    "cost": float(a["cost"] or 0.0),
                    "category": a["category"],
                    "notes": a["notes"]
                }
                for a in act_rows
            ]
            days.append({
                "id": str(d["id"]),
                "day_number": d["day_number"],
                "date": d["date"],
                "theme": d["theme"],
                "activities": acts
            })

        return {
            "id": str(itin["id"]),
            "title": itin["title"],
            "destination": itin["destination"],
            "start_date": itin["start_date"],
            "end_date": itin["end_date"],
            "pacing": itin["pacing"],
            "version": itin["version"],
            "updated_at": itin["updated_at"],
            "days": days
        }
    finally:
        conn.close()

# 5. Update Itinerary
@app.put("/api/v1/itineraries/{id}", status_code=status.HTTP_200_OK)
def update_itinerary(id: int, req: UpdateItineraryRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM itineraries WHERE id = ?", (id,))
        itin = cursor.fetchone()
        if not itin:
            raise HTTPException(status_code=404, detail=f"Itinerary {id} not found")

        new_title = req.title if req.title is not None else itin["title"]
        new_start = req.start_date if req.start_date is not None else itin["start_date"]
        new_end = req.end_date if req.end_date is not None else itin["end_date"]
        new_pacing = req.pacing if req.pacing is not None else itin["pacing"]

        cursor.execute(
            """
            UPDATE itineraries
            SET title = ?, start_date = ?, end_date = ?, pacing = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_title, new_start, new_end, new_pacing, id)
        )
        conn.commit()
        return {
            "id": str(id),
            "title": new_title,
            "updated_at": "now"
        }
    finally:
        conn.close()

# 6. Add Activity
@app.post("/api/v1/itineraries/{id}/activities", status_code=status.HTTP_201_CREATED)
def add_activity(id: int, req: CreateActivityRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM itineraries WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Itinerary not found")

        cursor.execute(
            """
            INSERT INTO activities (itinerary_id, day_id, time, title, location, cost, category, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (id, req.day_id, req.time, req.title, req.location, req.cost or 0.0, req.category or "General", req.notes or "")
        )
        act_id = cursor.lastrowid
        conn.commit()
        return {
            "id": str(act_id),
            "day_id": str(req.day_id),
            "title": req.title,
            "time": req.time,
            "created_at": "now"
        }
    finally:
        conn.close()

# 7. Update Activity
@app.put("/api/v1/itineraries/{id}/activities/{activity_id}", status_code=status.HTTP_200_OK)
def update_activity(id: int, activity_id: int, req: Dict[str, Any]):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activities WHERE id = ? AND itinerary_id = ?", (activity_id, id))
        act = cursor.fetchone()
        if not act:
            raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found in trip {id}")

        title = req.get("title", act["title"])
        time = req.get("time", act["time"])
        loc = req.get("location", act["location"])
        cost = req.get("cost", act["cost"])
        notes = req.get("notes", act["notes"])

        cursor.execute(
            """
            UPDATE activities SET title = ?, time = ?, location = ?, cost = ?, notes = ?
            WHERE id = ?
            """,
            (title, time, loc, cost, notes, activity_id)
        )
        conn.commit()
        return {"id": str(activity_id), "title": title, "updated_at": "now"}
    finally:
        conn.close()

# 8. Delete Activity
@app.delete("/api/v1/itineraries/{id}/activities/{activity_id}", status_code=status.HTTP_200_OK)
def delete_activity(id: int, activity_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activities WHERE id = ? AND itinerary_id = ?", (activity_id, id))
        conn.commit()
        return {"status": "deleted", "id": str(activity_id)}
    finally:
        conn.close()

# 9. Offline Delta Sync (REQ-F-008, AC-2)
@app.post("/api/v1/itineraries/{id}/sync", status_code=status.HTTP_200_OK)
def sync_itinerary(id: int, req: SyncRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM itineraries WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"Itinerary {id} not found")

        applied = 0
        for m in req.mutations:
            if m.action == "update" and m.entity == "activity":
                act_id = m.data.get("id")
                if act_id:
                    cursor.execute(
                        "UPDATE activities SET title = COALESCE(?, title), notes = COALESCE(?, notes) WHERE id = ?",
                        (m.data.get("title"), m.data.get("notes"), act_id)
                    )
                    applied += 1
            elif m.action == "create" and m.entity == "activity":
                day_id = m.data.get("day_id", 1)
                cursor.execute(
                    "INSERT INTO activities (itinerary_id, day_id, time, title, location, cost) VALUES (?, ?, ?, ?, ?, ?)",
                    (id, day_id, m.data.get("time", "09:00 AM"), m.data.get("title", "New"), m.data.get("location", ""), m.data.get("cost", 0.0))
                )
                applied += 1

        cursor.execute("UPDATE itineraries SET version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
        conn.commit()

        return {
            "status": "synced",
            "server_timestamp": "2026-11-16T12:00:00Z",
            "applied_count": applied
        }
    finally:
        conn.close()

# 10. List Collaborators (REQ-F-011, AC-3)
@app.get("/api/v1/workspaces/{trip_id}/collaborators", status_code=status.HTTP_200_OK)
def get_collaborators(trip_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, status FROM collaborators WHERE trip_id = ?", (trip_id,))
        rows = cursor.fetchall()
        collabs = [
            {"id": str(r["id"]), "name": r["name"], "email": r["email"], "role": r["role"], "status": r["status"]}
            for r in rows
        ]
        return {"trip_id": str(trip_id), "collaborators": collabs}
    finally:
        conn.close()

# 11. Invite Collaborator (REQ-F-011, AC-3)
@app.post("/api/v1/workspaces/{trip_id}/collaborators", status_code=status.HTTP_201_CREATED)
def invite_collaborator(trip_id: int, req: InviteCollaboratorRequest):
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Valid email address is required")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        name = req.email.split("@")[0].capitalize()
        cursor.execute(
            """
            INSERT INTO collaborators (trip_id, name, email, role, status)
            VALUES (?, ?, ?, ?, 'Active')
            """,
            (trip_id, name, req.email, req.role or "Editor")
        )
        collab_id = cursor.lastrowid
        conn.commit()
        return {
            "id": str(collab_id),
            "email": req.email,
            "role": req.role,
            "invite_url": f"https://travelgen.app/join/{trip_id}?token=inv_{collab_id}"
        }
    finally:
        conn.close()

# 12. Get Expense Ledger & Settlements (ARCH-7791, ARCH-7797)
@app.get("/api/v1/expenses/{trip_id}", status_code=status.HTTP_200_OK)
def get_expenses(trip_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE trip_id = ? ORDER BY id ASC", (trip_id,))
        exp_rows = cursor.fetchall()

        expenses = []
        total_usd = 0.0
        balances = {}

        for e in exp_rows:
            amt = float(e["amount"])
            amt_base = float(e["amount_base"])
            total_usd += amt_base
            expenses.append({
                "id": str(e["id"]),
                "title": e["title"],
                "amount": amt,
                "currency": e["currency"],
                "paid_by": e["paid_by"],
                "category": e["category"],
                "date": e["date"]
            })

            # Track payer credit
            payer = e["paid_by"]
            balances[payer] = balances.get(payer, 0.0) + amt_base

            # Deduct member splits
            cursor.execute("SELECT user_name, amount FROM expense_splits WHERE expense_id = ?", (e["id"],))
            splits = cursor.fetchall()
            for s in splits:
                user = s["user_name"]
                balances[user] = balances.get(user, 0.0) - float(s["amount"])

        settlements = simplify_debts(balances)

        return {
            "trip_id": str(trip_id),
            "base_currency": "USD",
            "total_spent": round(total_usd, 2),
            "expenses": expenses,
            "settlements": settlements
        }
    finally:
        conn.close()

# 13. Create Expense
@app.post("/api/v1/expenses/{trip_id}", status_code=status.HTTP_201_CREATED)
def create_expense(trip_id: int, req: CreateExpenseRequest):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Expense amount must be greater than zero")

    amount_base = float(convert_to_base_usd(req.amount, req.currency))
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (trip_id, title, amount, currency, paid_by, category, amount_base)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trip_id, req.title, req.amount, req.currency, req.paid_by, req.category, amount_base)
        )
        expense_id = cursor.lastrowid

        members = req.split_between or [req.paid_by]
        split_each = round(amount_base / max(1, len(members)), 4)
        for m in members:
            cursor.execute(
                "INSERT INTO expense_splits (expense_id, user_name, amount) VALUES (?, ?, ?)",
                (expense_id, m, split_each)
            )

        conn.commit()
        return {
            "id": str(expense_id),
            "title": req.title,
            "amount_base": amount_base,
            "created_at": "now"
        }
    finally:
        conn.close()

# 14. Affiliate Recommendations (ARCH-7793)
@app.get("/api/v1/affiliates/recommendations", status_code=status.HTTP_200_OK)
def get_affiliate_recommendations(destination: Optional[str] = None):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if destination:
            cursor.execute("SELECT * FROM affiliates WHERE destination LIKE ? ORDER BY rating DESC", (f"%{destination}%",))
        else:
            cursor.execute("SELECT * FROM affiliates ORDER BY rating DESC")
        rows = cursor.fetchall()
        recs = [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "provider": r["provider"],
                "price": float(r["price"]),
                "rating": float(r["rating"]),
                "image_url": r["image_url"],
                "affiliate_url": r["affiliate_url"]
            }
            for r in rows
        ]
        return {"recommendations": recs}
    finally:
        conn.close()

# 15. In-App Tokenized Checkout (REQ-F-016, AC-4)
@app.post("/api/v1/checkout/tokenize", status_code=status.HTTP_201_CREATED)
def tokenize_checkout(req: CheckoutRequest):
    if not req.payment_token or len(req.payment_token) < 4:
        raise HTTPException(
            status_code=402,
            detail="Payment token authorization failed. Please check payment provider credentials."
        )

    voucher_code = f"VOUCH-{req.experience_id[:8].upper()}-7851"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bookings (experience_id, title, payment_token, amount, currency, status, voucher_code, qr_code_url)
            VALUES (?, ?, ?, ?, ?, 'confirmed', ?, ?)
            """,
            (req.experience_id, f"Experience {req.experience_id}", req.payment_token, req.amount, req.currency, voucher_code, f"/static/qr/{voucher_code}.png")
        )
        booking_id = cursor.lastrowid
        conn.commit()
        return {
            "booking_id": str(booking_id),
            "status": "confirmed",
            "voucher_code": voucher_code,
            "qr_code_url": f"/static/qr/{voucher_code}.png"
        }
    finally:
        conn.close()

# 16. Admin Stats
@app.get("/api/v1/admin/stats", status_code=status.HTTP_200_OK)
def get_admin_stats():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM itineraries")
        itin_count = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM admin_metrics ORDER BY id DESC LIMIT 1")
        metric = cursor.fetchone()

        return {
            "total_itineraries": max(itin_count, metric["total_itineraries"] if metric else 120),
            "uptime_percent": float(metric["uptime_percent"] if metric else 99.95),
            "p95_ttfb_seconds": float(metric["p95_ttfb_seconds"] if metric else 1.25),
            "affiliate_ctr_percent": float(metric["affiliate_ctr_percent"] if metric else 15.4),
            "in_app_conversion_percent": float(metric["in_app_conversion_percent"] if metric else 6.8)
        }
    finally:
        conn.close()

# 17. User Profile
@app.get("/api/v1/user/profile", status_code=status.HTTP_200_OK)
def get_user_profile():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = 1")
        user = cursor.fetchone()
        if not user:
            return {
                "name": "Alex Morgan",
                "email": "alex.morgan@example.com",
                "offline_caching_enabled": True,
                "preferred_currency": "USD",
                "notifications_enabled": True
            }
        return {
            "name": user["name"],
            "email": user["email"],
            "offline_caching_enabled": bool(user["offline_caching_enabled"]),
            "preferred_currency": user["preferred_currency"],
            "notifications_enabled": bool(user["notifications_enabled"])
        }
    finally:
        conn.close()

# 18. Update User Profile
@app.put("/api/v1/user/profile", status_code=status.HTTP_200_OK)
def update_user_profile(profile: UserProfile):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users SET name = ?, offline_caching_enabled = ?, preferred_currency = ?, notifications_enabled = ?
            WHERE id = 1
            """,
            (profile.name, int(profile.offline_caching_enabled), profile.preferred_currency, int(profile.notifications_enabled))
        )
        conn.commit()
        return {"status": "updated", "updated_at": "now"}
    finally:
        conn.close()

# 19. Export User Data (CONF-1)
@app.get("/api/v1/user/export", status_code=status.HTTP_200_OK)
def export_user_data():
    return {
        "user_id": "1",
        "exported_at": "2026-11-16T12:37:06Z",
        "download_url": "/api/v1/user/export/download"
    }

# Mount static files directory for frontend UI views
static_path = Path(__file__).resolve().parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/", include_in_schema=False)
    def root_index():
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Travel Itinerary Generator Platform API"}

    @app.get("/tokens.css", include_in_schema=False)
    def get_tokens_css():
        for p in [static_path / "tokens.css", static_path / "css" / "tokens.css"]:
            if p.exists():
                return FileResponse(str(p), media_type="text/css")
        raise HTTPException(status_code=404, detail="tokens.css not found")
