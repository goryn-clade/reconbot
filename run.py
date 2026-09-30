import schedule
import time
import os
import yaml

from reconbot.tasks import esi_notification_task
from reconbot.notifiers.caching import CachingNotifier
from reconbot.notifiers.discordwebhook import DiscordWebhookNotifier
from reconbot.notifiers.splitter import SplitterNotifier
from reconbot.apiqueue import ApiQueue
from reconbot.esi import ESI
from reconbot.sso import SSO
from dotenv import load_dotenv

load_dotenv()

notification_caching_timer  = 10
webhook_url                 = os.getenv("WEBHOOK_URL")
sso_app_client_id           = os.getenv("SSO_APP_CLIENT_ID")
sso_app_secret_key          = os.getenv("SSO_APP_SECRET_KEY")

with open('./characters.yaml') as file:
    # The FullLoader parameter handles the conversion from YAML
    # scalar values to Python the dictionary format
    characters_list = yaml.load(file)

discord = {
    'webhook': {
        'url': webhook_url
    }
}

sso_app = {
    'client_id': sso_app_client_id,
    'secret_key': sso_app_secret_key
}


notifications = {
    'whitelist': [
        'AllWarDeclaredMsg',
        'DeclareWar',
        'AllWarInvalidatedMsg',
        'AllyJoinedWarAggressorMsg',
        'CorpWarDeclaredMsg',
        'OwnershipTransferred',
        'MoonminingExtractionStarted',
        'MoonminingExtractionCancelled',
        'MoonminingExtractionFinished',
        'SovStructureDestroyed',
        'SovStructureReinforced',
        'StructureUnderAttack',
        'OwnershipTransferred',
        'StructureOnline',
        # 'StructureFuelAlert',
        'StructureAnchoring',
        'StructureServicesOffline',
        'StructureLostShields',
        'StructureLostArmor',
        'TowerAlertMsg',
        'StationServiceEnabled',
        'StationServiceDisabled',
        'SovAllClaimAquiredMsg',
        'SovStationEnteredFreeport',
        'SovAllClaimLostMsg',
        'SovStructureSelfDestructRequested',
        'SovStructureSelfDestructFinished',
        'StationConquerMsg',
        'EntosisCaptureStarted',
    ]
}

my_discord_channels = CachingNotifier(
    SplitterNotifier([
        DiscordWebhookNotifier(
            discord['webhook']['url']
        )
    ]),
    duration=7200
)

def api_to_sso(api):
    return SSO(
        sso_app['client_id'],
        sso_app['secret_key'],
        api['refresh_token'],
        api['character_id']
    )

api_queue_logistics = ApiQueue(list(map(api_to_sso, characters_list.values())))

def notifications_job_logistics():
    esi_notification_task(
        notifications,
        api_queue_logistics,
        'discord',
        my_discord_channels
    )

def run_and_schedule(characters, notifications_job):
    notifications_job()
    schedule.every(notification_caching_timer/len(characters)).minutes.do(notifications_job)

run_and_schedule(characters_list, notifications_job_logistics)

while True:
    schedule.run_pending()
    time.sleep(1)
