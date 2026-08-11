from datetime import datetime,timedelta
from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

# users in chat application.
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    name: str
    created_at : datetime = Field(default_factory=datetime.utcnow)   # for storing the time when user is created
    

# for storing messages between conversation memebers.
class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    user_id: int = Field(foreign_key="users.id")
    conversation_id:int = Field(foreign_key = "conversations.id")   # to link the message with a conversation
    created_at:datetime = Field(default_factory=datetime.utcnow)


# represents one chat in a conversation. can have multiple chats as well
class Conversation(SQLModel,table=True):
    __tablename__ = "conversations"
    id:Optional[int] = Field (default = None, primary_key  = True)   # for storing the id of conversation
    name:str = Field(index=True,unique=True) # for storing name of conversation(family,friends etc)
    type:str # group chat or private
    owner: int = Field (foreign_key = "users.id") # to link the conversation with a owner/user. This is optional if you have only one type of conversations like family,friends etc
    created_at : datetime = Field (default_factory = datetime.utcnow)   # for storing the time when conversation is created    



# stores who belongs to each conversation
class ConversationMember(SQLModel, table=True):
    # for storing the members of a conversation.  This is optional if you have only one type of conversations like family or friends etc    
    __tablename__ = "conversation_members"   # name of our database Table. This is optional if you have only one type conversation like family or friends etc
    id : Optional[int] = Field (default=None, primary_key=True)  # unique id for each member in the conversation.
    user_id : Optional[int] = Field (foreign_key="users.id")  # foreign key to link with user table    
    role:str # member/owner/admin and so on
    conversation_id : Optional[int] = Field (foreign_key="conversations.id")  # foreign key to link with conversation table    
    joined_at: datetime = Field (default_factory = datetime.utcnow )   # for storing the time when member joined or left a conversation    
    

# for storing otp's
class OTP(SQLModel, table=True):
    __tablename__ = "otps"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True)
    hash: str # hashed otp code.
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    created_at:datetime = Field(default_factory=datetime.utcnow)




# decoded Payload
class TokenData(SQLModel):
    user_id:int

# user response
class UserResponse(SQLModel):
    name:str
    email:EmailStr

# message response 
class MessageResponse(SQLModel):
    id:int
    content:str
    sender_id:str
    

# otp request
class OTPRequest(SQLModel):
    name:str
    email:EmailStr

# otp verify
class VerifyOtp(SQLModel):
    otp_code:str
    email:EmailStr
    
# token Response
class TokenResponse(SQLModel, schema=True):  # for access and refresh tokens.  
    access_token : str 
    refresh_token : str
    token_type:str = "bearer"