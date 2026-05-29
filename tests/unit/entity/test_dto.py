import pytest

from entity.dto import ChatType, TelegramMessageDTO


@pytest.fixture()
def sample_dto() -> TelegramMessageDTO:
    return TelegramMessageDTO(
        message_id=42,
        chat_id=100,
        username="johndoe",
        text="hello",
        chat_type="private",
    )


class TestTelegramMessageDTOInit:
    def test_telegram_message_dto_init_sets_message_id_correctly(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act - fixture handles construction

        # assert
        assert sample_dto.message_id == 42

    def test_telegram_message_dto_init_sets_chat_id_correctly(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act

        # assert
        assert sample_dto.chat_id == 100

    def test_telegram_message_dto_init_sets_username_correctly(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act

        # assert
        assert sample_dto.username == "johndoe"

    def test_telegram_message_dto_init_sets_text_correctly(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act

        # assert
        assert sample_dto.text == "hello"

    def test_telegram_message_dto_init_sets_chat_type_correctly(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act

        # assert
        assert sample_dto.chat_type == "private"

    def test_telegram_message_dto_init_with_none_message_id_is_valid(self) -> None:
        # arrange / act
        dto = TelegramMessageDTO(
            message_id=None,
            chat_id=1,
            username="user",
            text="reply",
            chat_type="private",
        )

        # assert - Optional[int] must accept None (used for outgoing replies)
        assert dto.message_id is None


class TestTelegramMessageDTOStr:
    def test_telegram_message_dto_str_contains_message_id(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = str(sample_dto)

        # assert
        assert "42" in result

    def test_telegram_message_dto_str_contains_chat_id(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = str(sample_dto)

        # assert
        assert "100" in result

    def test_telegram_message_dto_str_contains_username(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = str(sample_dto)

        # assert
        assert "johndoe" in result

    def test_telegram_message_dto_str_contains_text(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = str(sample_dto)

        # assert
        assert "hello" in result

    def test_telegram_message_dto_str_contains_chat_type(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = str(sample_dto)

        # assert
        assert "private" in result

    def test_telegram_message_dto_repr_matches_str(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act

        # assert - dataclass __str__ delegates to __repr__
        assert repr(sample_dto) == str(sample_dto)


class TestTelegramMessageDTOSerialize:
    def test_telegram_message_dto_serialize_returns_dict(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = sample_dto.serialize()

        # assert
        assert isinstance(result, dict)

    def test_telegram_message_dto_serialize_contains_all_keys(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = sample_dto.serialize()

        # assert
        assert set(result.keys()) == {"message_id", "chat_id", "chat_type", "username", "text"}

    def test_telegram_message_dto_serialize_values_match_fields(
        self, sample_dto: TelegramMessageDTO
    ) -> None:
        # arrange / act
        result = sample_dto.serialize()

        # assert
        assert result["message_id"] == 42
        assert result["chat_id"] == 100
        assert result["username"] == "johndoe"
        assert result["text"] == "hello"
        assert result["chat_type"] == "private"

    def test_telegram_message_dto_serialize_with_none_message_id_returns_none(self) -> None:
        # arrange
        dto = TelegramMessageDTO(
            message_id=None, chat_id=1, username="u", text="t", chat_type="private"
        )

        # act
        result = dto.serialize()

        # assert
        assert result["message_id"] is None


class TestChatType:
    def test_chat_type_private_value_is_correct(self) -> None:
        # arrange / act / assert
        assert ChatType.PRIVATE == "private"

    def test_chat_type_group_value_is_correct(self) -> None:
        # arrange / act / assert
        assert ChatType.GROUP == "group"

    def test_chat_type_supergroup_value_is_correct(self) -> None:
        # arrange / act / assert
        assert ChatType.SUPERGROUP == "supergroup"

    def test_chat_type_channel_value_is_correct(self) -> None:
        # arrange / act / assert
        assert ChatType.CHANNEL == "channel"

    def test_chat_type_is_string_comparable(self) -> None:
        # strEnum values must behave as plain strings for comparisons in handlers

        # arrange / act / assert
        assert ChatType.PRIVATE == "private"
