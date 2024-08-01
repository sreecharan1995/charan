# coding: utf-8

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.package_reference_model import PackageReferenceModel


class ImportSummaryModel(BaseModel):
    """Model to represent the result of an import operation.
    
    When an xml file including package list and bundles is imported, the result is his import summary, that contains counts for data being processed or failures.
    """

    profileName: str = ""
    previousPackages: int = 0
    includedPackages: int = 0
    missedPackages: int = 0
    ignoredPackages: int = 0
    importedBundles: int = 0
    importFailedBundles: int = 0
    previousBundles: int = 0
    includedBundles: int = 0
    missedBundles: int = 0
    ignoredBundles: int = 0
    errors: int = 0

class InvalidPackageReference(BaseModel):

    name: Optional[str] = None
    version: Optional[str] = None
    issue: Optional[str] = None

InvalidPackageReference.update_forward_refs()    


class InvalidBundle(BaseModel):
    
    name: Optional[str] = None
    packages: Optional[List[InvalidPackageReference]] = None
    issue: str

InvalidBundle.update_forward_refs()    

class PackagesImportReport(BaseModel):

    previous: List[PackageReferenceModel] = []
    included: List[PackageReferenceModel] = []
    missed: List[InvalidPackageReference] = []
    ignored: List[str] = []

PackagesImportReport.update_forward_refs()

class BundlesImportReport(BaseModel):

    imported: List[BundleModel] = []
    previous: List[BundleModel] = []
    included: List[BundleModel] = []
    missed: List[InvalidBundle] = []
    ignored: List[str] = []

BundlesImportReport.update_forward_refs()

class ImportReport(BaseModel):
    """ImportReport - a report summarizing an xml import process outcome"""

    ...    
    packages: PackagesImportReport = PackagesImportReport()
    bundles: BundlesImportReport = BundlesImportReport()

    summary: ImportSummaryModel = ImportSummaryModel()
    errors: List[str] = []

    def has_issues(self) -> bool:        
        return (
            len(self.errors) > 0
            or len(self.packages.ignored) > 0
            or len(self.packages.missed) > 0
            or len(self.bundles.ignored) > 0
            or len(self.bundles.missed) > 0
        )

    def count(self):
        self.summary.errors = len(self.errors)
        self.summary.ignoredPackages = len(self.packages.ignored)
        self.summary.missedPackages = len(self.packages.missed)
        self.summary.includedPackages = len(self.packages.included)
        self.summary.previousPackages = len(self.packages.previous)
        self.summary.ignoredBundles = len(self.bundles.ignored)
        self.summary.missedBundles = len(self.bundles.missed)
        self.summary.importedBundles = len(self.bundles.imported)
        self.summary.includedBundles = len(self.bundles.included)
        self.summary.previousBundles = len(self.bundles.previous)

ImportReport.update_forward_refs()
