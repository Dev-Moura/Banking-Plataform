from datetime import date, datetime


def date_para_str(data: date) -> str:
    return data.strftime("%d/%m/%Y")


def str_para_date(data: str) -> date:
    return datetime.strftime(data, "%d/%m/%Y")


def formatar_flaot_str_moeda(valor: float) -> str:
    return f"R$ {valor:.2f}"
