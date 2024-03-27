from amocrm.v2 import Lead as _Lead
from amocrm.v2 import custom_field
from config import Config


class Lead(_Lead):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    utm_content = custom_field.BaseCustomField("utm_content", field_id=Config.lead_utm_content_field_id, code="UTM_CONTENT")
    utm_medium = custom_field.BaseCustomField("utm_medium", field_id=Config.lead_utm_medium_field_id, code="UTM_MEDIUM")
    utm_campaign = custom_field.BaseCustomField("utm_campaign", field_id=Config.lead_utm_campaign_field_id, code="UTM_CAMPAIGN")
    utm_source = custom_field.BaseCustomField("utm_source", field_id=Config.lead_utm_source_field_id, code="UTM_SOURCE")
    utm_term = custom_field.BaseCustomField("utm_term", field_id=Config.lead_utm_term_field_id, code="UTM_TERM")
    utm_referrer = custom_field.BaseCustomField("utm_referrer", field_id=Config.lead_utm_referrer_field_id, code="UTM_REFERRER")
    roistat = custom_field.BaseCustomField("roistat", field_id=Config.lead_roistat_field_id, code="ROISTAT")
    openstat_service = custom_field.BaseCustomField("openstat_service", field_id=Config.lead_openstat_service_field_id, code="OPENSTAT_SERVICE")
    openstat_campaign = custom_field.BaseCustomField("openstat_campaign", field_id=Config.lead_openstat_campaign_field_id, code="OPENSTAT_CAMPAIGN")
    openstat_ad = custom_field.BaseCustomField("openstat_ad", field_id=Config.lead_openstat_ad_field_id, code="OPENSTAT_AD")
    openstat_source = custom_field.BaseCustomField("openstat_source", field_id=Config.lead_openstat_source_field_id, code="OPENSTAT_SOURCE")
    roistat_user = custom_field.TextCustomField("roistat", field_id=Config.lead_roistat_user_field_id)
    id_subscription_payments = custom_field.TextCustomField("ID абонемента для оплаты", field_id=Config.lead_id_subscription_payments_field_id)
    id_subscription_lessons = custom_field.TextCustomField("ID абонемента для уроков", field_id=Config.lead_id_subscription_lessons_field_id)
    id_subscription_paid_promo = custom_field.TextCustomField("ID абонементов для оплаты платных промоуроков", field_id=Config.lead_id_subscription_paid_promo_field_id)
    promoter = custom_field.TextCustomField("ПРОМОУТЕР (ОФФЛАЙН)", field_id=1409163)
    promoter_location = custom_field.TextCustomField("ЛОКАЦИЯ (ОФФЛАЙН)", field_id=1409165)
    supervisor = custom_field.TextCustomField("СУПЕРВАЙЗЕР ПРОМОУТЕРА", field_id=1418477)
    direction = custom_field.TextCustomField("Направление", field_id=1416905)
    direction_type = custom_field.TextCustomField("Формат купленного абонемента", field_id=1416907)

