from interface.event_type import EventType


class TestEventType:
    def test_event_type_incoming_telegram_message_value_is_correct(self) -> None:
        # arrange / act / assert
        assert EventType.INCOMING_TELEGRAM_MESSAGE == "INCOMING_TELEGRAM_MESSAGE"

    def test_event_type_incoming_telegram_command_value_is_correct(self) -> None:
        # arrange / act / assert
        assert EventType.INCOMING_TELEGRAM_COMMAND == "INCOMING_TELEGRAM_COMMAND"

    def test_event_type_send_telegram_message_value_is_correct(self) -> None:
        # arrange / act / assert
        assert EventType.SEND_TELEGRAM_MESSAGE == "SEND_TELEGRAM_MESSAGE"

    def test_event_type_members_are_string_comparable(self) -> None:
        # strenum values must behave as plain strings for dict-key lookups in the bus

        # arrange / act
        mapping = {EventType.INCOMING_TELEGRAM_MESSAGE: "hit"}

        # assert
        assert mapping["INCOMING_TELEGRAM_MESSAGE"] == "hit"

