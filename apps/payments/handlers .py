def event_list():
    """
    Retorna a lista de eventos suportados
    """     
    return [
        'charge.antifraud_reproved',
        'charge.paid',
        'charge.partial_canceled',
        'charge.payment_failed',
        'charge.pending',
        'charge.processing',
        'charge.refunded'
    ]


def handle_webhook(payload):
    """
    Função handler para processar webhooks de pagamento
    """
    # Segurança mínima
    event = payload.get("type")

    if not event:
        return {"error": "Evento não informado"}, 400

