"""Vacancy search API with full filtering and export."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import csv
import io

from app.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.services.hh_client import HHClient

router = APIRouter()


# ============ Dictionaries ============


@router.get("/dictionaries")
async def get_dictionaries():
    """Get HH.ru dictionaries (experience, employment, schedule, etc.)."""
    client = HHClient()
    return await client.get_dictionaries()


@router.get("/areas")
async def get_areas():
    """Get all regions/areas (hierarchical)."""
    client = HHClient()
    return await client.get_areas()


@router.get("/areas/russia")
async def get_russia_areas():
    """Get Russia regions with cities."""
    client = HHClient()
    areas = await client.get_areas()
    # Find Russia (id=113)
    for country in areas:
        if country.get("id") == "113":
            return country
    return {"error": "Russia not found"}


@router.get("/professional-roles")
async def get_professional_roles():
    """Get professional roles (job categories)."""
    client = HHClient()
    return await client.get_professional_roles()


@router.get("/industries")
async def get_industries():
    """Get industries list."""
    client = HHClient()
    return await client.get_industries()


# ============ Vacancy Search ============


class SearchParams(BaseModel):
    """Search parameters model."""
    text: str | None = None
    area: list[str] | None = None
    salary: int | None = None
    only_with_salary: bool = False
    experience: str | None = None
    employment: list[str] | None = None
    schedule: list[str] | None = None
    professional_role: list[str] | None = None
    industry: list[str] | None = None
    search_field: list[str] | None = None
    period: int | None = None
    order_by: str = "relevance"


@router.get("/vacancies")
async def search_vacancies(
    text: str | None = None,
    area: list[str] | None = Query(default=None),
    salary: int | None = None,
    only_with_salary: bool = False,
    experience: str | None = None,
    employment: list[str] | None = Query(default=None),
    schedule: list[str] | None = Query(default=None),
    professional_role: list[str] | None = Query(default=None),
    industry: list[str] | None = Query(default=None),
    search_field: list[str] | None = Query(default=None),
    period: int | None = None,
    order_by: str = "relevance",
    page: int = 0,
    per_page: int = 20,
):
    """Search vacancies with filters."""
    client = HHClient()
    return await client.search_vacancies_full(
        text=text,
        area=area,
        salary=salary,
        only_with_salary=only_with_salary,
        experience=experience,
        employment=employment,
        schedule=schedule,
        professional_role=professional_role,
        industry=industry,
        search_field=search_field,
        period=period,
        order_by=order_by,
        page=page,
        per_page=per_page,
    )


@router.post("/vacancies/export")
async def export_vacancies(
    params: SearchParams,
    format: str = "json",
    max_pages: int = 20,
):
    """Export all vacancies matching search criteria.

    Args:
        params: Search parameters
        format: Export format (json or csv)
        max_pages: Maximum pages to fetch (up to 2000 vacancies)
    """
    client = HHClient()

    # Build search params dict
    search_params = {}
    if params.text:
        search_params["text"] = params.text
    if params.area:
        search_params["area"] = params.area
    if params.salary:
        search_params["salary"] = params.salary
    if params.only_with_salary:
        search_params["only_with_salary"] = params.only_with_salary
    if params.experience:
        search_params["experience"] = params.experience
    if params.employment:
        search_params["employment"] = params.employment
    if params.schedule:
        search_params["schedule"] = params.schedule
    if params.professional_role:
        search_params["professional_role"] = params.professional_role
    if params.industry:
        search_params["industry"] = params.industry
    if params.search_field:
        search_params["search_field"] = params.search_field
    if params.period:
        search_params["period"] = params.period
    if params.order_by:
        search_params["order_by"] = params.order_by

    # Export all vacancies
    vacancies = await client.export_all_vacancies(max_pages=max_pages, **search_params)

    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Название", "Компания", "Город", "Зарплата от", "Зарплата до",
            "Валюта", "Опыт", "Занятость", "График", "URL", "Дата публикации"
        ])

        # Data
        for v in vacancies:
            salary = v.get("salary") or {}
            area = v.get("area") or {}
            employer = v.get("employer") or {}
            experience = v.get("experience") or {}
            employment = v.get("employment") or {}
            schedule = v.get("schedule") or {}

            writer.writerow([
                v.get("id", ""),
                v.get("name", ""),
                employer.get("name", ""),
                area.get("name", ""),
                salary.get("from", ""),
                salary.get("to", ""),
                salary.get("currency", ""),
                experience.get("name", ""),
                employment.get("name", ""),
                schedule.get("name", ""),
                v.get("alternate_url", ""),
                v.get("published_at", ""),
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vacancies.csv"}
        )
    else:
        # JSON format
        return {
            "total": len(vacancies),
            "items": vacancies,
        }


@router.get("/vacancies/{vacancy_id}")
async def get_vacancy_details(vacancy_id: str):
    """Get full vacancy details."""
    client = HHClient()
    return await client.get_vacancy(vacancy_id)
