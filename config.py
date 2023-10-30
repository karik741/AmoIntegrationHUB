import os
from typing import Any

import consul
import yaml


class ConfigType:
    allowed_phones = []
    client_id = None
    client_secret = None
    subdomain = None
    redirect_url = None
    token_directory = None
    broker_url = None
    docrm_url = None
    task_queue = None
    utc_delta_seconds = 0
    web_port = 0
    code = None

    # Настройки АМО
    primary_leads_pipeline_id = 0
    lead_status_new_lead_value_id = 0
    lead_status_contacted_value_id = 0
    lead_status_not_contacted_value_id = 0
    lead_status_missed_promo_value_id = 0
    lead_status_visited_promo_value_id = 0
    lead_status_primary_payed_for_course_value_id = 0
    lead_status_primary_rejection = 0
    lead_status_payed_for_promo_value_id = 0
    lead_status_prepayed_for_course_value_id = 0
    lead_status_need_identified_value_id = 0
    lead_status_recorded_to_promo_value_id = 0
    lead_primary_loss_reason_not_payed = 0
    lead_primary_loss_reason_in_rejection = 0
    lead_primary_loss_reason_visit_promo_not_payed = 0

    secondary_leads_pipeline_id = 0
    lead_status_secondary_payed_value_id = 0
    lead_status_secondary_prepayed_value_id = 0
    lead_status_secondary_rejection = 0
    lead_status_needs_schedule_value_id = 0
    lead_status_fullpayed_for_course_value_id = 0
    lead_status_zero_lessons_remained_value_id = 0
    lead_status_in_schedule_value_id: 0

    event_leads_pipeline_id = 0
    lead_status_payed_ticket = 0
    lead_status_came_event = 0

    task_type_cc_processing_site_value_id = 0
    task_type_cc_promo_register_value_id = 0
    task_type_cc_promo_reregister_value_id = 0
    task_type_promo_retro_value_id = 0
    task_type_cc_recall_value_id = 0
    task_type_fullpay_value_id = 0
    task_type_register_new_value_id = 0
    task_type_fill_info_value_id = 0
    task_type_renew_value_id = 0
    task_type_confirmation = 0
    use_confirmation_tasks = 0

    user_free_cc_tasks_holder_id = 0
    user_sales_person_id = 0
    user_admin_id = 0
    user_admin_1_id = 0
    user_admin_2_id = 0
    user_sales_leader_online_id = 0
    uses_sales_offl = 0
    user_technician_id = 0

    lead_statuses_exclude = [0]
    lead_utm_content_field_id = 0
    lead_utm_medium_field_id = 0
    lead_utm_campaign_field_id = 0
    lead_utm_source_field_id = 0
    lead_utm_term_field_id = 0
    lead_utm_referrer_field_id = 0
    lead_roistat_field_id = 0
    lead_openstat_service_field_id = 0
    lead_openstat_campaign_field_id = 0
    lead_openstat_ad_field_id = 0
    lead_openstat_source_field_id = 0
    lead_roistat_user_field_id = 0
    lead_id_subscription_payments_field_id = 0
    lead_id_subscription_lessons_field_id = 0
    lead_id_subscription_paid_promo_field_id = 0

    client_docrm_uuid_field_id = 0
    client_email_field_id = 0
    client_visited_trial_lesson_field_id = 0
    client_last_visited_trial_lesson_date_field_id = 0
    client_last_visited_trial_lesson_direction_field_id = 0
    client_has_prepaid_field_id = 0
    client_last_prepaid_date_field_id = 0
    client_last_prepaid_sum_field_id = 0
    client_has_full_paid_field_id = 0
    client_full_paid_date_field_id = 0
    client_last_deal_paid_sum_field_id = 0
    client_paid_group_count_field_id = 0
    client_paid_individual_count_field_id = 0
    client_paid_sum_full_field_id = 0
    client_has_active_group_deal_field_id = 0
    client_has_active_individual_deal_field_id = 0
    client_is_in_schedule_field_id = 0
    client_is_in_group_schedule_field_id = 0
    client_is_in_individual_schedule_field_id = 0
    client_last_group_lesson_visit_date_field_id = 0
    client_last_group_deal_end_date_field_id = 0
    client_remained_group_lesson_count_field_id = 0
    client_last_record_date_field_id = 0
    client_last_receive_time_field_id = 0
    client_last_group_lesson_visit_direction_field_id = 0
    client_last_individual_lesson_visit_date_field_id = 0
    client_last_individual_lesson_visit_teacher_field_id = 0
    client_remained_individual_lesson_count_field_id = 0
    client_last_cancelled_record_date_field_id = 0
    client_last_group_lesson_visit_teacher_field_id = 0
    client_last_visited_trial_lesson_teacher_field_id = 0
    client_visited_trial_yes_value_id = 0
    client_visited_trial_no_value_id = 0
    client_has_prepaid_yes_value_id = 0
    client_has_prepaid_no_value_id = 0
    client_has_full_paid_yes_value_id = 0
    client_has_full_paid_no_value_id = 0
    client_has_active_group_deal_yes_value_id = 0
    client_has_active_group_deal_no_value_id = 0
    client_has_active_individual_deal_yes_value_id = 0
    client_has_active_individual_deal_no_value_id = 0
    client_is_in_schedule_yes_value_id = 0
    client_is_in_schedule_no_value_id = 0
    client_is_in_group_schedule_yes_value_id = 0
    client_is_in_group_schedule_no_value_id = 0
    client_is_in_individual_schedule_yes_value_id = 0
    client_is_in_individual_schedule_no_value_id = 0
    settings_task_type_fullpay_to_current_manager = False
    settings_task_type_promo_retro_to_current_manager = False
    settings_task_type_reregister_to_current_manager = False
    db_url = 0

    def whitelist_enabled(self):
        return len(self.allowed_phones) > 0

    def load(self, cfg: Any):
        config = yaml.safe_load(cfg)
        self.code = config.get('code', None)
        self.client_id = config['client_id']
        self.task_queue = config['task_queue']
        self.client_secret = config['client_secret']
        self.subdomain = config['subdomain']
        self.redirect_url = config['redirect_url']
        self.token_directory = config['token_directory']
        self.broker_url = config['broker_url']
        self.docrm_url = config['docrm_url']
        self.utc_delta_seconds = config['utc_delta_seconds']
        self.web_port = config['web_port']

        self.primary_leads_pipeline_id = config['primary_leads_pipeline_id']
        self.lead_status_new_lead_value_id = config['lead_status_new_lead_value_id']
        self.lead_status_contacted_value_id = config['lead_status_contacted_value_id']
        self.lead_status_not_contacted_value_id = config['lead_status_not_contacted_value_id']
        self.lead_status_missed_promo_value_id = config['lead_status_missed_promo_value_id']
        self.lead_status_visited_promo_value_id = config['lead_status_visited_promo_value_id']
        self.lead_status_primary_rejection = config['lead_status_primary_rejection']
        self.lead_status_primary_payed_for_course_value_id = config['lead_status_primary_payed_for_course_value_id']
        self.lead_status_payed_for_promo_value_id = config['lead_status_payed_for_promo_value_id']
        self.lead_status_prepayed_for_course_value_id = config['lead_status_prepayed_for_course_value_id']
        self.lead_status_need_identified_value_id = config['lead_status_need_identified_value_id']
        self.lead_status_recorded_to_promo_value_id = config['lead_status_recorded_to_promo_value_id']
        self.lead_primary_loss_reason_not_payed = config['lead_primary_loss_reason_not_payed']
        self.lead_primary_loss_reason_in_rejection = config['lead_primary_loss_reason_in_rejection']
        self.lead_primary_loss_reason_visit_promo_not_payed = config['lead_primary_loss_reason_visit_promo_not_payed']

        self.secondary_leads_pipeline_id = config['secondary_leads_pipeline_id']
        self.lead_status_secondary_payed_value_id = config['lead_status_secondary_payed_value_id']
        self.lead_status_secondary_prepayed_value_id = config['lead_status_secondary_prepayed_value_id']
        self.lead_status_secondary_rejection = config['lead_status_secondary_rejection']
        self.lead_status_needs_schedule_value_id = config['lead_status_needs_schedule_value_id']
        self.lead_status_fullpayed_for_course_value_id = config['lead_status_fullpayed_for_course_value_id']
        self.lead_status_zero_lessons_remained_value_id = config['lead_status_zero_lessons_remained_value_id']
        self.lead_status_in_schedule_value_id = config['lead_status_in_schedule_value_id']

        self.event_leads_pipeline_id = config['event_leads_pipeline_id']
        self.lead_status_payed_ticket = config['lead_status_payed_ticket']
        self.lead_status_came_event = config['lead_status_came_event']

        self.task_type_cc_processing_site_value_id = config['task_type_cc_processing_site_value_id']
        self.task_type_cc_promo_register_value_id = config['task_type_cc_promo_register_value_id']
        self.task_type_cc_promo_reregister_value_id = config['task_type_cc_promo_reregister_value_id']
        self.task_type_promo_retro_value_id = config['task_type_promo_retro_value_id']
        self.task_type_cc_recall_value_id = config['task_type_cc_recall_value_id']
        self.task_type_fullpay_value_id = config['task_type_fullpay_value_id']
        self.task_type_register_new_value_id = config['task_type_register_new_value_id']
        self.task_type_fill_info_value_id = config['task_type_fill_info_value_id']
        self.task_type_renew_value_id = config['task_type_renew_value_id']
        self.task_type_confirmation = config['task_type_confirmation']
        self.use_confirmation_tasks = config['use_confirmation_tasks']

        self.user_free_cc_tasks_holder_id = config['user_free_cc_tasks_holder_id']
        self.user_sales_person_id = config['user_sales_person_id']
        self.user_admin_id = config['user_admin_id']
        self.user_admin_1_id = config['user_admin_1_id']
        self.user_admin_2_id = config['user_admin_2_id']
        self.user_sales_leader_online_id = config['user_sales_leader_online_id']
        self.uses_sales_offl = config['uses_sales_offl']
        self.user_technician_id = config['user_technician_id']

        self.lead_statuses_exclude = config['lead_statuses_exclude']
        self.lead_utm_content_field_id = config['lead_utm_content_field_id']
        self.lead_utm_medium_field_id = config['lead_utm_medium_field_id']
        self.lead_utm_campaign_field_id = config['lead_utm_campaign_field_id']
        self.lead_utm_source_field_id = config['lead_utm_source_field_id']
        self.lead_utm_term_field_id = config['lead_utm_term_field_id']
        self.lead_utm_referrer_field_id = config['lead_utm_referrer_field_id']
        self.lead_roistat_field_id = config['lead_roistat_field_id']
        self.lead_openstat_service_field_id = config['lead_openstat_service_field_id']
        self.lead_openstat_campaign_field_id = config['lead_openstat_campaign_field_id']
        self.lead_openstat_ad_field_id = config['lead_openstat_ad_field_id']
        self.lead_openstat_source_field_id = config['lead_openstat_source_field_id']
        self.lead_roistat_user_field_id = config['lead_roistat_user_field_id']
        self.lead_id_subscription_payments_field_id = config['lead_id_subscription_payments_field_id']
        self.lead_id_subscription_lessons_field_id = config['lead_id_subscription_lessons_field_id']
        self.lead_id_subscription_paid_promo_field_id = config['lead_id_subscription_paid_promo_field_id']

        self.client_docrm_uuid_field_id = config['client_docrm_uuid_field_id']
        self.client_email_field_id = config['client_email_field_id']
        self.client_visited_trial_lesson_field_id = config['client_visited_trial_lesson_field_id']
        self.client_last_visited_trial_lesson_date_field_id = config['client_last_visited_trial_lesson_date_field_id']
        self.client_last_visited_trial_lesson_direction_field_id = config[
            'client_last_visited_trial_lesson_direction_field_id']
        self.client_has_prepaid_field_id = config['client_has_prepaid_field_id']
        self.client_last_prepaid_date_field_id = config['client_last_prepaid_date_field_id']
        self.client_last_prepaid_sum_field_id = config['client_last_prepaid_sum_field_id']
        self.client_has_full_paid_field_id = config['client_has_full_paid_field_id']
        self.client_full_paid_date_field_id = config['client_full_paid_date_field_id']
        self.client_last_deal_paid_sum_field_id = config['client_last_deal_paid_sum_field_id']
        self.client_paid_group_count_field_id = config['client_paid_group_count_field_id']
        self.client_paid_individual_count_field_id = config['client_paid_individual_count_field_id']
        self.client_paid_sum_full_field_id = config['client_paid_sum_full_field_id']
        self.client_has_active_group_deal_field_id = config['client_has_active_group_deal_field_id']
        self.client_has_active_individual_deal_field_id = config['client_has_active_individual_deal_field_id']
        self.client_is_in_schedule_field_id = config['client_is_in_schedule_field_id']
        self.client_is_in_group_schedule_field_id = config['client_is_in_group_schedule_field_id']
        self.client_is_in_individual_schedule_field_id = config['client_is_in_individual_schedule_field_id']
        self.client_last_group_lesson_visit_date_field_id = config['client_last_group_lesson_visit_date_field_id']
        self.client_last_group_deal_end_date_field_id = config['client_last_group_deal_end_date_field_id']
        self.client_remained_group_lesson_count_field_id = config['client_remained_group_lesson_count_field_id']
        self.client_last_record_date_field_id = config['client_last_record_date_field_id']
        self.client_last_receive_time_field_id = config['client_last_receive_time_field_id']
        self.client_last_group_lesson_visit_direction_field_id = config[
            'client_last_group_lesson_visit_direction_field_id']
        self.client_last_individual_lesson_visit_date_field_id = config[
            'client_last_individual_lesson_visit_date_field_id']
        self.client_last_individual_lesson_visit_teacher_field_id = config[
            'client_last_individual_lesson_visit_teacher_field_id']
        self.client_remained_individual_lesson_count_field_id = config[
            'client_remained_individual_lesson_count_field_id']
        self.client_last_cancelled_record_date_field_id = config['client_last_cancelled_record_date_field_id']
        self.client_last_group_lesson_visit_teacher_field_id = config['client_last_group_lesson_visit_teacher_field_id']
        self.client_last_visited_trial_lesson_teacher_field_id = config[
            'client_last_visited_trial_lesson_teacher_field_id']
        self.client_visited_trial_yes_value_id = config['client_visited_trial_yes_value_id']
        self.client_visited_trial_no_value_id = config['client_visited_trial_no_value_id']
        self.client_has_prepaid_yes_value_id = config['client_has_prepaid_yes_value_id']
        self.client_has_prepaid_no_value_id = config['client_has_prepaid_no_value_id']
        self.client_has_full_paid_yes_value_id = config['client_has_full_paid_yes_value_id']
        self.client_has_full_paid_no_value_id = config['client_has_full_paid_no_value_id']
        self.client_has_active_group_deal_yes_value_id = config['client_has_active_group_deal_yes_value_id']
        self.client_has_active_group_deal_no_value_id = config['client_has_active_group_deal_no_value_id']
        self.client_has_active_individual_deal_yes_value_id = config['client_has_active_individual_deal_yes_value_id']
        self.client_has_active_individual_deal_no_value_id = config['client_has_active_individual_deal_no_value_id']
        self.client_is_in_schedule_yes_value_id = config['client_is_in_schedule_yes_value_id']
        self.client_is_in_schedule_no_value_id = config['client_is_in_schedule_no_value_id']
        self.client_is_in_group_schedule_yes_value_id = config['client_is_in_group_schedule_yes_value_id']
        self.client_is_in_group_schedule_no_value_id = config['client_is_in_group_schedule_no_value_id']
        self.client_is_in_individual_schedule_yes_value_id = config['client_is_in_individual_schedule_yes_value_id']
        self.client_is_in_individual_schedule_no_value_id = config['client_is_in_individual_schedule_no_value_id']
        self.settings_task_type_fullpay_to_current_manager = config['settings_task_type_fullpay_to_current_manager']
        self.settings_task_type_promo_retro_to_current_manager = \
            config['settings_task_type_promo_retro_to_current_manager']
        self.settings_task_type_reregister_to_current_manager = \
            config['settings_task_type_reregister_to_current_manager']
        self.db_url = config['db_url']


Config = ConfigType()

consul_host = os.environ.get('CONSUL_HOST', None)
consul_token = os.environ.get('CONSUL_TOKEN', None)
consul_config_key = os.environ.get('CONSUL_CONFIG_KEY', None)
amo_config = os.environ.get('AMO_CONFIG', None)

if consul_host and consul_token and consul_config_key:
    client = consul.Consul(host=consul_host, token=consul_token)
    index, result = client.kv.get(consul_config_key, index=None)
    Config.load(result['Value'])
elif amo_config:
    with open(amo_config) as cfg_file:
        Config.load(cfg_file)


def save():
    if consul_host and consul_token and consul_config_key:
        client = consul.Consul(host=consul_host, token=consul_token)
        client.kv.put(consul_config_key, yaml.dump(vars(Config)))

