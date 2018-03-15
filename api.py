from app import app
import watson_developer_cloud
from flask import Flask, request, jsonify
from models import Conversation
from playhouse.shortcuts import model_to_dict
from twilio.twiml.voice_response import Gather, VoiceResponse, Say



workspace_id='98a14852-01ec-4e2e-b13b-555c860bdd6a'
@app.route('/dialog/schedule/')
def dialog_schedule():
    conv = None
    first = True 
    conv_id = request.args.get('conversation_id','')
    app.logger.info('request with conversation_id = %s', conv_id)
    if conv_id:
         conv = Conversation.get_by_id(conv_id)
         first = False
    else:
         conv = Conversation.create(context={})
    input_msg = request.args.get('input','')
    context = conv.context
    result={}
    conversation = watson_developer_cloud.ConversationV1(
        username='7c11236a-ed0b-4980-8ac3-4cf02ce83e10',
        password='vnLi336yQI4T',
        version='2018-03-12'
    )
    response = conversation.message(
        workspace_id = workspace_id,
        input = {
            'text': input_msg 
        },
        context=(context if not first else None)
    ) 
    if 'context' in response:
        conv.context = response['context'] 
        print(conv.context)
        conv.save()
        result={
            'id': conv.id,
            'output': response['output']['text']
        }
    return jsonify(result) 

def new_conversation():
    return watson_developer_cloud.ConversationV1(
        username='7c11236a-ed0b-4980-8ac3-4cf02ce83e10',
        password='vnLi336yQI4T',
        version='2018-03-12'
    )

def new_conversation_msg(conversation, input_msg="", context=None, first=True):
    return conversation.message(
        workspace_id = workspace_id,
        input = {
            'text': input_msg 
        },
        context=(context if not first else None)
    )

def create_response(watson_response, conv, twilio_voice=None):
    if 'context' in watson_response:
        conv.context = watson_response['context'] 
        app.logger.info(conv.context)
        watson_dialog = ' '.join(watson_response['output']['text'])
        twilio_voice.say(watson_dialog, voice='alice', language='en-US')
        twilio_voice.gather(input='speech')
    else:
        watson_dialog = 'I am sorry we are currently experiencing issues please call again later'
        twilio_voice.say(watson_dialog, voice='alice', language='en-US')
        twilio_voice.hangup()
    return twilio_voice

@app.route('/voice/schedule/', methods=['GET', 'POST'])
def voice_schedule():
    print(request.form)
    call_sid = request.form['CallSid']
    if not call_sid:
        return 'Unable to respond', 404
    app.logger.info('request with call sid = %s', call_sid)
    conv, created = Conversation.get_or_create(call_sid=call_sid)
    resp = VoiceResponse()
    if created:
        app.logger.info('new conversation created')
        conv.call_country = request.form['CallerCountry']
        conv.call_state = request.form['CallerState']
        conv.call_number = request.form['Caller']
        conv.call_city = request.form['CallerCity']
        conv.call_zip = request.form['CallerZip']
        app.logger.info('creating ibm cloud conversation')
        conversation = new_conversation()
        # send message to watson
        app.logger.info('creating a new conversation with watson!')
        watson_response = new_conversation_msg(conversation)
        # generate twilio response
        create_response(watson_response, conv, twilio_voice=resp)
        conv.save()
    else:
        input_msg = request.form['SpeechResult'] if 'SpeechResult' in request.form else 'donno' 
        app.logger.info('conversation found and input message is "%s"', input_msg)
        # send message to watson
        conversation = new_conversation()
        watson_response = new_conversation_msg(conversation, context=conv.context, input_msg=input_msg, first=False)
        # generate twilio response
        create_response(watson_response, conv, twilio_voice=resp)
    return str(resp)
