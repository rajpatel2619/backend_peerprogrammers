from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Boolean   
from sqlalchemy.orm import relationship
from ..connection.database import Base

class Domain(Base):
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    subdomains = relationship("Subdomain", back_populates="domain")
    resources = relationship("Resource", back_populates="domain")


class Subdomain(Base):
    __tablename__ = "subdomains"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)

    domain = relationship("Domain", back_populates="subdomains")
    resources = relationship("Resource", back_populates="subdomain")

    __table_args__ = (
        UniqueConstraint("name", "domain_id", name="uq_subdomain_per_domain"),
    )


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000))
    link = Column(String(500))
    upvote = Column(Integer, default=0)
    downvote = Column(Integer, default=0)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    subdomain_id = Column(Integer, ForeignKey("subdomains.id"), nullable=False)
    
    # Added fields
    added_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_verified = Column(Boolean, default=False)

    domain = relationship("Domain", back_populates="resources")
    subdomain = relationship("Subdomain", back_populates="resources")
    user = relationship('User', back_populates='resources')