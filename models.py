from pydantic import BaseModel, Field
from datetime import datetime


class BaseData(BaseModel):
    """Base model for all data types"""
    searched_at: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    search_keywords: str = ""
    search_location: str | None = None

    class Config:
        extra = "allow"

    def get_key_field(self) -> str:
        """Get the primary key field for this model"""
        return "id"

    def get_key_value(self) -> str:
        """Get the primary key value for this model"""
        return getattr(self, self.get_key_field())


class ProfileData(BaseData):
    profile_url: str
    name: str = ""
    headline: str = ""
    location: str = ""
    about: str = ""
    current_company: str = ""
    connection_sent: bool = False
    connection_sent_at: str | None = None
    message_sent: bool = False

    def get_key_field(self) -> str:
        return "profile_url"

    def get_key_value(self) -> str:
        return self.profile_url


class CompanyData(BaseData):
    company_url: str
    name: str = ""
    company_id: str = ""
    industry: str = ""
    location: str = ""
    company_size: str = ""
    summary: str = ""

    def get_key_field(self) -> str:
        return "company_url"

    def get_key_value(self) -> str:
        return self.company_url


class JobData(BaseData):
    job_id: str
    job_url: str
    title: str = ""
    company: str = ""
    location: str = ""
    posted_time: str = ""
    posted_datetime: str = ""
    is_promoted: bool = False
    easy_apply: bool = False
    description: str = ""
    applicants: str = ""

    def get_key_field(self) -> str:
        return "job_id"

    def get_key_value(self) -> str:
        return self.job_id


class ConversationData(BaseModel):
    message_sent: str
    timestamp: float
    has_response: bool = False
    user_name: str
    voice_sent: bool = False
    voice_responses: dict[str, str] | None = Field(default=None)
