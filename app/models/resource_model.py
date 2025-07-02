from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..connection.database import Base

class Domain(Base):
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Add length

    subdomains = relationship("Subdomain", back_populates="domain")
    resources = relationship("Resource", back_populates="domain")


class Subdomain(Base):
    __tablename__ = "subdomains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Add length
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)

    domain = relationship("Domain", back_populates="subdomains")
    resources = relationship("Resource", back_populates="subdomain")


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)              # Add length
    description = Column(String(1000))                       # Optional
    link = Column(String(500))                               # Add length
    upvote = Column(Integer, default=0)
    downvote = Column(Integer, default=0)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=False)

    domain = relationship("Domain", back_populates="resources")
    subdomain = relationship("Subdomain", back_populates="resources")
