""" Message Type Definitions, organized by class
"""

class CONN:
    """ Connetion Class of Message Types.

        This type notation is still being discussed and may change.
    """
    OFFER = "urn:sovrin:agent:message_type:sovrin.org/connection_offer"
    REQUEST = "urn:sovrin:agent:message_type:sovrin.org/connection_request"
    RESPONSE = "urn:sovrin:agent:message_type:sovrin.org/connection_response"
    REJECTION = "urn:sovrin:agent:message_type:sovrin.org/connection_rejection"
    ACKNOWLEDGE = "urn:sovrin:agent:message_type:sovrin.org/connection_acknowledge"
    SENDER_REJECTION = "urn:sovrin:agent:message_type:sovrin.org/sender_offer_rejection"
    RECEIVER_REJECTION = "urn:sovrin:agent:message_type:sovrin.org/receiver_offer_rejection"

class UI:
    STATE = "urn:sovrin:agent:message_type:sovrin.org/ui/state"
    STATE_REQUEST = "urn:sovrin:agent:message_type:sovrin.org/ui/state_request"
    SEND_OFFER = "urn:sovrin:agent:message_type:sovrin.org/ui/send_offer"
    SEND_OFFER_ACCEPTED = "urn:sovrin:agent:message_type:sovrin.org/ui/send_offer_accepted"
    SENDER_SEND_OFFER_REJECTED = "urn:sovrin:agent:message_type:sovrin.org/ui/sender_send_offer_rejected"
    RECEIVER_SEND_OFFER_REJECTED = "urn:sovrin:agent:message_type:sovrin.org/ui/receiver_send_offer_rejected"
    SENDER_OFFER_REJECTED = "urn:sovrin:agent:message_type:sovrin.org/ui/sender_offer_rejected"
    RECEIVER_OFFER_REJECTED = "urn:sovrin:agent:message_type:sovrin.org/ui/receiver_offer_rejected"
    SEND_CONN_REJECTED = "urn:sovrin:agent:message_type:sovrin.org/ui/send_connection_rejected"
    INITIALIZE = "urn:sovrin:agent:message_type:sovrin.org/ui/initialize"
    OFFER_RECEIVED = "urn:sovrin:agent:message_type:sovrin.org/ui/offer_received"
    OFFER_SENT = "urn:sovrin:agent:message_type:sovrin.org/ui/offer_sent"
    OFFER_ACCEPTED = "urn:sovrin:agent:message_type:sovrin.org/ui/offer_accepted"
    OFFER_ACCEPTED_SENT = "urn:sovrin:agent:message_type:sovrin.org/ui/offer_accepted_sent"
    CONN_REJECTED = "urn:sovrin:agent:message_type:sovrin.org/ui/connection_rejected"