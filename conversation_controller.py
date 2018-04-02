from datetime import datetime, timedelta
from app import app
from pprint import pformat, pprint 
import watson_developer_cloud
from flask import request, jsonify
from models import Conversation, Business, Customer, Appointment
from playhouse.shortcuts import model_to_dict
from twilio.twiml.voice_response import Gather, VoiceResponse, Say


workspace_id='98a14852-01ec-4e2e-b13b-555c860bdd6a'
def new_conversation():
    app.logger.info('setting up watson cloud API')
    return watson_developer_cloud.ConversationV1(
        username='7c11236a-ed0b-4980-8ac3-4cf02ce83e10',
        password='vnLi336yQI4T',
        version='2018-03-12'
    )

def new_conversation_msg(conversation, input_msg="", context=None, first=True):
    app.logger.info(f'sending cloud API message [{input_msg}] context [{context} first [{first}] ')
    return conversation.message(
        workspace_id = workspace_id,
        input = {
            'text': input_msg 
        },
        context=(context if not first else None)
    )

def create_response(watson_response, conv, twilio_voice=None):
    watson_dialog=None
    #print('****************************')
    #print(pformat(watson_response))
    #print('****************************')
    if 'context' in watson_response:
        conv.context = watson_response['context'] 
        #app.logger.info(pformat(conv.context))
        watson_dialog = '. '.join(watson_response['output']['text'])
        twilio_voice.say(watson_dialog, voice='alice', language='en-US')
        twilio_voice.gather(input='speech')
    else:
        watson_dialog = 'I am sorry we are currently experiencing issues please call again later'
        twilio_voice.say(watson_dialog, voice='alice', language='en-US')
        twilio_voice.hangup()
    return twilio_voice, watson_dialog

def create_error_response(msg, twilio_voice=None):
    twilio_voice.say(msg, voice='alice', language='en-US')
    twilio_voice.hangup()
    return str(twilio_voice) 

def process_iden_conversation(msg, created=True, conv=None):
    resp = VoiceResponse()
    app.logger.info('customer is registered')
    conversation = new_conversation()
    if created:
        input_msg=''
    else:
        input_msg=request.form['SpeechResult'] if 'SpeechResult' in request.form else 'donno'
    app.logger.info('input_message [%s] created [%s]', input_msg, created)
    #conv.log_json()
    watson_response = new_conversation_msg(conversation, context=conv.context, input_msg=input_msg, first=False)
    conv.store_context()
    # check if watson identified the customer
    twilio_resp, watson_dialog = create_response(watson_response, conv, twilio_voice=resp)
    app.logger.info('output_message [%s] ', watson_dialog)
    if 'action' in conv.context:
        if conv.context['action'] == 'register_customer':
            cust=Customer.create(
                name=str(conv.context['name']).lower(),
                business=conv.business,
                phone=conv.call_number
            )
            conv.customer = cust
        elif conv.context['action'] == 'create_app':
            app_date = conv.context['app_date']
            app_time = conv.context['app_time']
            start = datetime.strptime(f"{app_date} {app_time}", '%Y-%m-%d %H:%M:%S')
            end = start+timedelta(hours=float(conv.context['app_duration']))
            appoint = Appointment(
                customer=conv.customer,
                note='tutoring',
                start=start,
                end=end
            )
            app.logger.info(f"created a new appointment {start} to {end}")
            appoint.save()
            conv.context['success'] = 'true'
        elif conv.context['action'] == 'end':
            twilio_resp.hangup()
        conv.context.pop('action', None)
    conv.save()
    return str(resp)


def process_voice_scheduling():
    call_sid = request.form['CallSid']
    if not call_sid:
        return 'Unable to respond', 404
    app.logger.info('request with call sid = %s', call_sid)
    conv, created, msg = Conversation.get_or_new(request.form, call_sid=call_sid)

    # if no conversation could be generated, this can happen because there is no
    # business registered on the line
    if not conv:
        app.logger.info('business is not registered')
        return create_error_response(msg, twilio_voice=resp)

    # if need to register customer
    if not conv.identity_affirmed():
        if not conv.customer:
            # could not find the customer on our DB
            return process_iden_conversation("customer is not registered", created=created, conv=conv)
        else:
            # identified the customer on our DB
            return process_iden_conversation("customer is registered", created=created, conv=conv)

    return process_iden_conversation("eventhing else", created=False, conv=conv)
