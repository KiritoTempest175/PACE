"""SQLite locally or persistent hosted PostgreSQL, with tenant-scoped queries."""
from __future__ import annotations
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4
from sqlalchemy import create_engine, String, Text, ForeignKey, select, delete, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from core.config import get_settings

class Base(DeclarativeBase):
    pass

class Conversation(Base):
    __tablename__ = 'conversations'
    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    workspace: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)

class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(48), ForeignKey('conversations.id', ondelete='CASCADE'), index=True)
    role: Mapped[str] = mapped_column(String(12))
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40))

_lock = Lock()
_engine = None
_Session = None

def _sessionmaker():
    global _engine, _Session
    if _Session is None:
        with _lock:
            if _Session is None:
                url = get_settings().database_url
                options = {'check_same_thread': False} if url.startswith('sqlite:') else {}
                _engine = create_engine(url, pool_pre_ping=True, connect_args=options)
                if url.startswith('sqlite:'):
                    @event.listens_for(_engine, 'connect')
                    def enable_fk(dbapi_conn, record):
                        dbapi_conn.execute('PRAGMA foreign_keys=ON')
                _Session = sessionmaker(_engine, expire_on_commit=False)
    return _Session

def init_db():
    _sessionmaker()
    Base.metadata.create_all(_engine)

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def create_conversation(owner: str, title: str, workspace: str) -> dict:
    record = Conversation(id='chat-'+str(uuid4()), owner=owner, title=title, workspace=workspace, created_at=now(), updated_at=now())
    with _sessionmaker().begin() as db:
        db.add(record)
    return conversation_dict(record)

def conversation_dict(c: Conversation) -> dict:
    return {k:getattr(c,k) for k in ('id','title','workspace','created_at','updated_at')}

def message_dict(m: Message) -> dict:
    return {k:getattr(m,k) for k in ('id','role','text','source','status','created_at')}

def list_conversations(owner: str) -> list[dict]:
    with _sessionmaker()() as db:
        items=db.scalars(select(Conversation).where(Conversation.owner==owner).order_by(Conversation.updated_at.desc()).limit(100)).all()
        return [{**conversation_dict(i), 'document_id': attached_document(owner, i.id)} for i in items]

def get_conversation(owner: str, cid: str) -> dict | None:
    with _sessionmaker()() as db:
        c=db.scalar(select(Conversation).where(Conversation.owner==owner, Conversation.id==cid))
        if c is None: return None
        msgs=db.scalars(select(Message).where(Message.conversation_id==cid).order_by(Message.created_at)).all()
        return {**conversation_dict(c), 'document_id': attached_document(owner, cid), 'messages':[message_dict(m) for m in msgs]}

def delete_conversation(owner: str, cid: str) -> bool:
    with _sessionmaker().begin() as db:
        c=db.scalar(select(Conversation).where(Conversation.owner==owner,Conversation.id==cid))
        if c is None: return False
        db.execute(delete(Message).where(Message.conversation_id==cid))
        db.execute(delete(ConversationDocument).where(ConversationDocument.conversation_id==cid))
        db.delete(c)
        return True

def add_message(owner: str, cid: str, role: str, text: str, source: str='pace', status: str='completed') -> dict | None:
    with _sessionmaker().begin() as db:
        c=db.scalar(select(Conversation).where(Conversation.owner==owner, Conversation.id==cid))
        if c is None: return None
        record=Message(id='msg-'+str(uuid4()),conversation_id=cid,role=role,text=text,source=source,status=status,created_at=now())
        db.add(record)
        c.updated_at=now()
        db.flush()
        return message_dict(record)

def reset_db_for_tests():
    """Only for test fixtures; never invoke from HTTP endpoints."""
    global _engine,_Session
    if _engine is not None: _engine.dispose()
    _engine=None;_Session=None

class Document(Base):
    __tablename__='documents'
    id: Mapped[str] = mapped_column(String(48),primary_key=True)
    owner: Mapped[str] = mapped_column(String(64),index=True)
    name: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40))

class ConversationDocument(Base):
    """Keeps selected literacy document across page reload and chat navigation."""
    __tablename__ = 'conversation_documents'
    conversation_id: Mapped[str] = mapped_column(String(48), ForeignKey('conversations.id', ondelete='CASCADE'), primary_key=True)
    owner: Mapped[str] = mapped_column(String(64), index=True)
    document_id: Mapped[str] = mapped_column(String(48), ForeignKey('documents.id', ondelete='CASCADE'))


def attach_document(owner: str, cid: str, did: str) -> None:
    with _sessionmaker().begin() as db:
        convo = db.scalar(select(Conversation).where(Conversation.owner == owner, Conversation.id == cid))
        doc = db.scalar(select(Document).where(Document.owner == owner, Document.id == did))
        if convo is None or doc is None:
            raise ValueError('Conversation or document does not belong to session')
        link = db.scalar(select(ConversationDocument).where(ConversationDocument.conversation_id == cid))
        if link is None:
            db.add(ConversationDocument(conversation_id=cid, document_id=did, owner=owner))
        else:
            link.document_id = did


def attached_document(owner: str, cid: str) -> str | None:
    with _sessionmaker()() as db:
        link = db.scalar(select(ConversationDocument).where(ConversationDocument.owner == owner, ConversationDocument.conversation_id == cid))
        return link.document_id if link else None


def save_document(owner: str, text: str) -> str:
    did='doc-'+str(uuid4())
    with _sessionmaker().begin() as db:
        db.add(Document(id=did,owner=owner,name='document.pdf',text=text,created_at=now()))
    return did

def get_document(owner: str, did: str) -> str | None:
    with _sessionmaker()() as db:
        doc=db.scalar(select(Document).where(Document.owner==owner, Document.id==did))
        return doc.text if doc is not None else None

def remove_document(owner: str, did: str) -> bool:
    with _sessionmaker().begin() as db:
        doc=db.scalar(select(Document).where(Document.owner==owner,Document.id==did))
        if doc is None: return False
        db.execute(delete(ConversationDocument).where(ConversationDocument.document_id == did))
        db.delete(doc)
        return True
