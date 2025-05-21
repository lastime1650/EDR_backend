
rule MAL_Telegram_C2_Communications
{
    meta:
        description = "Detects Telegram-based malware communicating with api.telegram.org"
        author = "whyyouwannasee"
        reference = "https://core.telegram.org/bots/api"
        date = "2025-05-20"
        category = "malware"
        tlp = "white"

        yarahub_uuid = "c446f948-e971-4e0e-844a-f9a2af442716"  
        yarahub_license = "CC0 1.0"
        yarahub_reference_md5 = "466b9beeb51926c9d9ae9d538a2da037"  
        yarahub_rule_matching_tlp = "TLP:WHITE"
        yarahub_rule_sharing_tlp = "TLP:WHITE"

    strings:
        $telegram_api_1 = "api.telegram.org" ascii wide nocase
        $telegram_api_2 = "hxxps://api.telegram.org" ascii wide nocase
        $telegram_api_3 = "api[.]telegram[.]org" ascii wide nocase

    condition:
        any of ($telegram_api*)
}
