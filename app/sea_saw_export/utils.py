"""Shared document formatting utilities for PI/PO generation."""

from django.conf import settings


def format_payment_terms(currency, deposit, balance) -> str:
    """Build a readable payment terms string from deposit/balance amounts."""
    parts = []
    if deposit is not None:
        parts.append(f"Deposit: {currency} {deposit:,.2f}")
    if balance is not None:
        parts.append(f"Balance: {currency} {balance:,.2f}")
    return ", ".join(parts) if parts else ""


def format_bank_details(bank_account, fallback_setting: str = "") -> str:
    """Build a pipe-separated bank details string from a BankAccount instance."""
    if bank_account is None:
        return getattr(settings, fallback_setting, "") if fallback_setting else ""

    parts = []
    account_name = (
        getattr(bank_account.account_holder, "account_name", None)
        if bank_account.account_holder
        else None
    )
    if account_name:
        parts.append(f"Beneficiary: {account_name}")
    if bank_account.bank_name:
        parts.append(f"Bank Name: {bank_account.bank_name}")
    if bank_account.bank_address:
        parts.append(f"Bank Address: {bank_account.bank_address}")
    if bank_account.account_number:
        parts.append(f"Account No: {bank_account.account_number}")
    if bank_account.swift_code:
        parts.append(f"SWIFT/BIC: {bank_account.swift_code}")
    if bank_account.branch:
        parts.append(f"Branch: {bank_account.branch}")
    return " | ".join(parts)
