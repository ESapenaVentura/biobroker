import datetime
from enum import Enum
from dateutil import parser
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field, field_validator, ConfigDict

"""
FIELDS/SUPPORTING MODELS
------------------------
"""


class CharacteristicsFields(BaseModel):
    model_config = ConfigDict(extra='forbid')
    text: str | datetime.datetime | int | float
    unit: Optional[str] = None
    ontologyTerms: Optional[list[str]] = None
    tag : Optional[str] = None

    @field_validator('text')
    @classmethod
    def proper_formats(cls, value):
        """
        Evaluate if an input is a date/int/float and give it a proper formatting, returning it as str
        """
        if isinstance(value, datetime.datetime):
            value = value.strftime("%Y-%m-%dT%H:%M:%SZ")
            if value.endswith('T00:00:00Z'):
                value = value.replace('T00:00:00Z', '')
            return value
        elif isinstance(value, float):
            return str(int(value)) if value.is_integer() else str(value)
        return str(value)

class DataContent(BaseModel):
    value: str

class DataEntry(BaseModel):
    webinSubmissionAccountId: str = Field(pattern="Webin-[0-9]+$")
    type: str
    content: list[Dict[str, DataContent]]

class RelationshipType(str, Enum):
    derived_from = "derived_from"
    same_as = "same_as"
    has_member = "has_member"
    child_of = "child_of"

class Relationship(BaseModel):
    model_config = ConfigDict(extra='forbid')
    target: str = Field(pattern="^SAMEA[0-9]+$")
    source: str = Field(pattern="^SAMEA[0-9]+$")
    type: RelationshipType

class Organization(BaseModel):
    Name: str

class ExternalUrl(BaseModel):
    url: str = Field(pattern="https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}([-a-zA-Z0-9()@:%_\+.~#?&\/=]*)")
    doi: Optional[str] = None

"""
DATA MODELS
-----------
"""

class StructuredDataModel(BaseModel):
    """
    Biosamples' structured data model
    """
    accession: str = Field(pattern="^SAME.[0-9]+$")
    data: list[DataEntry]

class BiosampleGeneralModel(BaseModel):
    """
    Biosamples General model
    """
    model_config = ConfigDict(extra='allow')
    name: str = Field(min_length=1)
    accession: Optional[str] = None
    release: str
    characteristics: Dict[str, list[CharacteristicsFields]]
    relationships: Optional[list[Relationship]] = None
    organization: Optional[list[Organization]] = None
    structuredData: Optional[list[DataEntry]] = None
    externalReferences: Optional[list[ExternalUrl]] = None

    @field_validator('release')
    @classmethod
    def parse_date(cls, value):
        try:
            value = parser.isoparse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError("Invalid date format. Should be provided as YYYY-MM-DD with optional Thh:mm:ss.sssZ") from None
        return value

    @field_validator('characteristics')
    @classmethod
    def organism_must_be_set(cls, value):
        valid_organism_keys = ('organism', 'Organism', 'species', 'Species')
        try:
            which_one = [key in value for key in valid_organism_keys]
            which_one.index(True)
        except ValueError:
            raise ValueError("'organism' must be set. Please use the keys 'organism', 'Organism', 'species' or 'Species'") from None
        value['organism'] = value[valid_organism_keys[which_one.index(True)]]
        for organism_key in valid_organism_keys[1:]:
            if organism_key in value:
                del value[organism_key]
        return value


class BiosampleGeneralEnaModel(BiosampleGeneralModel):
    @field_validator('characteristics')
    @classmethod
    def mandatory_ena_fields(cls, value):
        if not all([any([key in value for key in ('collection_date', 'collection date', 'Event Date/Time')]), 'geographic location (country and/or sea)' in value]):
            raise ValueError("'collection date' and 'geographic location (country and/or sea)' fields must be set for the sample")
        return value

class EnaLinkingField(BaseModel):
    accession: Optional[str] = None
    alias: Optional[str] = None # Add validator so that at least accession or alias is set


class ExperimentLibraryStrategy(Enum):
    wgs = "WGS"
    wga = "WGA"
    wxs = "WXS"
    rna_seq = "RNA-Seq"
    ssrna_seq = "ssRNA-seq"
    snrna_seq = "snRNA-seq"
    mirna_seq = "miRNA-Seq"
    ncrna_seq = "ncRNA-Seq"
    fl_cdna = "FL-cDNA"
    est = "EST"
    hi_c = "Hi-C"
    atac_seq = "ATAC-seq"
    wcs = "WCS"
    rad_seq = "RAD-Seq"
    clone = "CLONE"
    poolclone = "POOLCLONE"
    amplicon = "AMPLICON"
    cloneend = "CLONEEND"
    finishing = "FINISHING"
    chip_seq = "ChIP-Seq"
    mnase_seq = "MNase-Seq"
    dnase_hypersensitivity = "DNase-Hypersensitivity"
    bisulfite_seq = "Bisulfite-Seq"
    cts = "CTS"
    mre_seq = "MRE-Seq"
    medip_seq = "MeDIP-Seq"
    mbd_seq = "MBD-Seq"
    tn_seq = "Tn-Seq"
    validation = "VALIDATION"
    faire_seq = "FAIRE-seq"
    selex = "SELEX"
    rip_seq = "RIP-Seq"
    chia_pet = "ChIA-PET"
    synthetic_long_read = "Synthetic-Long-Read"
    targeted_capture = "Targeted-Capture"
    tethered_chromatin_conformation_capture = "Tethered Chromatin Conformation Capture"
    nome_seq = "NOMe-Seq"
    chm_seq = "ChM-Seq"
    gbs = "GBS"
    ribo_seq = "Ribo-Seq"
    other = "OTHER"


class ExperimentLibrarySource(Enum):
    genomic = "GENOMIC"
    genomic_single_cell = "GENOMIC SINGLE CELL"
    transcriptomic = "TRANSCRIPTOMIC"
    transcriptomic_single_cell = "TRANSCRIPTOMIC SINGLE CELL"
    metagenomic = "METAGENOMIC"
    metatranscriptomic = "METATRANSCRIPTOMIC"
    synthetic = "SYNTHETIC"
    viral_rna = "VIRAL RNA"
    other = "OTHER"

class ExperimentLibrarySelection(Enum):
    random = "RANDOM"
    pcr = "PCR"
    random_pcr = "RANDOM PCR"
    rt_pcr = "RT-PCR"
    hmpr = "HMPR"
    mf = "MF"
    repeat_fractionation = "repeat fractionation"
    size_fractionation = "size fractionation"
    msll = "MSLL"
    cdna = "cDNA"
    cdna_randompriming = "cDNA_randomPriming"
    cdna_oligo_dt = "cDNA_oligo_dT"
    polya = "PolyA"
    oligo_dt = "Oligo-dT"
    inverse_rrna = "Inverse rRNA"
    inverse_rrna_selection = "Inverse rRNA selection"
    chip = "ChIP"
    chip_seq = "ChIP-Seq"
    mnase = "MNase"
    dnase = "DNase"
    hybrid_selection = "Hybrid Selection"
    reduced_representation = "Reduced Representation"
    restriction_digest = "Restriction Digest"
    five_methylcytidine_antibody = "5-methylcytidine antibody"
    mbd2_protein_methyl_cpg_binding_domain = "MBD2 protein methyl-CpG binding domain"
    cage = "CAGE"
    race = "RACE"
    mda = "MDA"
    padlock_probes_capture_method = "padlock probes capture method"
    other = "other"
    unspecified = "unspecified"


class ExperimentLibraryLayout(Enum):
    single = "SINGLE"
    paired = "PAIRED"

class EnaLibraryDescriptor(BaseModel):
    libraryName: Optional[str] = None
    libraryStrategy: ExperimentLibraryStrategy
    librarySource: ExperimentLibrarySource
    librarySelection: ExperimentLibrarySelection
    libraryLayout: ExperimentLibraryLayout
    poolingStrategy: Optional[str] = None
    libraryConstructionProtocol: Optional[str] = None

class EnaInstrumentPlatform(Enum):
    bgiseq = "BGISEQ"
    capillary = "CAPILLARY"
    dnbseq = "DNBSEQ"
    element = "ELEMENT"
    genapsys = "GENAPSYS"
    genemind = "GENEMIND"
    helicos = "HELICOS"
    illumina = "ILLUMINA"
    ion_torrent = "ION_TORRENT"
    ls454 = "LS454"
    oxford_nanopore = "OXFORD_NANOPORE"
    pacbio_smrt = "PACBIO_SMRT"
    tapestri = "TAPESTRI"
    vela_diagnostics = "VELA_DIAGNOSTICS"
    ultima = "ULTIMA"

class EnaInstrumentModel(Enum):
    fourfivefour_gs = "454 GS"
    fourfivefour_gs_20 = "454 GS 20"
    fourfivefour_gs_flx = "454 GS FLX"
    fourfivefour_gs_flx_titanium = "454 GS FLX Titanium"
    fourfivefour_gs_flx_plus = "454 GS FLX+"
    fourfivefour_gs_junior = "454 GS Junior"
    ab_310_genetic_analyzer = "AB 310 Genetic Analyzer"
    ab_3130_genetic_analyzer = "AB 3130 Genetic Analyzer"
    ab_3130xl_genetic_analyzer = "AB 3130xL Genetic Analyzer"
    ab_3five00_genetic_analyzer = "AB 3500 Genetic Analyzer"
    ab_3five00xl_genetic_analyzer = "AB 3500xL Genetic Analyzer"
    ab_3730_genetic_analyzer = "AB 3730 Genetic Analyzer"
    ab_3730xl_genetic_analyzer = "AB 3730xL Genetic Analyzer"
    ab_fivefive00_genetic_analyzer = "AB 5500 Genetic Analyzer"
    ab_fivefive00xl_genetic_analyzer = "AB 5500xl Genetic Analyzer"
    ab_fivefive00xl_w_genetic_analysis_system = "AB 5500xl-W Genetic Analysis System"
    bgiseq_five0 = "BGISEQ-50"
    bgiseq_five00 = "BGISEQ-500"
    dnbseq_gfour00 = "DNBSEQ-G400"
    dnbseq_gfour00_fast = "DNBSEQ-G400 FAST"
    dnbseq_gfive0 = "DNBSEQ-G50"
    dnbseq_t7 = "DNBSEQ-T7"
    element_aviti = "Element AVITI"
    fastaseq_300 = "FASTASeq 300"
    genius = "GENIUS"
    gs111 = "GS111"
    genapsys_sequencer = "Genapsys Sequencer"
    genocare_1600 = "GenoCare 1600"
    genolab_m = "GenoLab M"
    gridion = "GridION"
    helicos_heliscope = "Helicos HeliScope"
    hiseq_x_five = "HiSeq X Five"
    hiseq_x_ten = "HiSeq X Ten"
    illumina_genome_analyzer = "Illumina Genome Analyzer"
    illumina_genome_analyzer_ii = "Illumina Genome Analyzer II"
    illumina_genome_analyzer_iix = "Illumina Genome Analyzer IIx"
    illumina_hiscansq = "Illumina HiScanSQ"
    illumina_hiseq_1000 = "Illumina HiSeq 1000"
    illumina_hiseq_1five00 = "Illumina HiSeq 1500"
    illumina_hiseq_2000 = "Illumina HiSeq 2000"
    illumina_hiseq_2five00 = "Illumina HiSeq 2500"
    illumina_hiseq_3000 = "Illumina HiSeq 3000"
    illumina_hiseq_four000 = "Illumina HiSeq 4000"
    illumina_hiseq_x = "Illumina HiSeq X"
    illumina_miseq = "Illumina MiSeq"
    illumina_miniseq = "Illumina MiniSeq"
    illumina_novaseq_6000 = "Illumina NovaSeq 6000"
    illumina_novaseq_x = "Illumina NovaSeq X"
    illumina_iseq_100 = "Illumina iSeq 100"
    ion_genestudio_sfive = "Ion GeneStudio S5"
    ion_genestudio_sfive_plus = "Ion GeneStudio S5 Plus"
    ion_genestudio_sfive_prime = "Ion GeneStudio S5 Prime"
    ion_torrent_genexus = "Ion Torrent Genexus"
    ion_torrent_pgm = "Ion Torrent PGM"
    ion_torrent_proton = "Ion Torrent Proton"
    ion_torrent_sfive = "Ion Torrent S5"
    ion_torrent_sfive_xl = "Ion Torrent S5 XL"
    mgiseq_2000rs = "MGISEQ-2000RS"
    minion = "MinION"
    nextseq_1000 = "NextSeq 1000"
    nextseq_2000 = "NextSeq 2000"
    nextseq_five00 = "NextSeq 500"
    nextseq_fivefive0 = "NextSeq 550"
    onso = "Onso"
    pacbio_rs = "PacBio RS"
    pacbio_rs_ii = "PacBio RS II"
    promethion = "PromethION"
    revio = "Revio"
    sentosa_sq301 = "Sentosa SQ301"
    sequel = "Sequel"
    sequel_ii = "Sequel II"
    sequel_iie = "Sequel IIe"
    tapestri = "Tapestri"
    ug_100 = "UG 100"
    unspecified = "unspecified"

class EnaAttribute(BaseModel):
    tag: str
    value: Any
    unit: Optional[str] = None

class EnaFileType(Enum):
    sra = "sra"
    srf = "srf"
    sff = "sff"
    fastq = "fastq"
    fasta = "fasta"
    tab = "tab"
    four5four_native = "454_native"
    four5four_native_seq = "454_native_seq"
    four5four_native_qual = "454_native_qual"
    helicos_native = "Helicos_native"
    illumina_native = "Illumina_native"
    illumina_native_seq = "Illumina_native_seq"
    illumina_native_prb = "Illumina_native_prb"
    illumina_native_int = "Illumina_native_int"
    illumina_native_qseq = "Illumina_native_qseq"
    illumina_native_scarf = "Illumina_native_scarf"
    solid_native = "SOLiD_native"
    solid_native_csfasta = "SOLiD_native_csfasta"
    solid_native_qual = "SOLiD_native_qual"
    pacbio_hdf5 = "PacBio_HDF5"
    bam = "bam"
    cram = "cram"
    completegenomics_native = "CompleteGenomics_native"
    oxfordnanopore_native = "OxfordNanopore_native"

class EnaFile(BaseModel):
    fileName: str
    fileType: EnaFileType
    checksum: Optional[str] = None
    readType: Optional[str] = None
    checksumMethod: Optional[str] = None

class ActionType(Enum):
    add = "ADD"
    modify = "MODIFY"

class EnaAction(BaseModel):
    type: ActionType
    holdUntilDate: Optional[str] = None

    @field_validator('holdUntilDate')
    @classmethod
    def parse_date(cls, value):
        try:
            value = parser.isoparse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError(
                "Invalid date format. Should be provided as YYYY-MM-DD with optional Thh:mm:ss.sssZ") from None
        return value

class EnaBaseModel(BaseModel):
    alias: str
    accession: Optional[str] = None
    identifiers: Optional[dict] = None
    centerName: Optional[str] = None
    title: Optional[str] = None
    attributes: Optional[list[EnaAttribute]] = None
    links: Optional[str] = None
    holdUntilDate: Optional[str] = None

    @field_validator('holdUntilDate')
    @classmethod
    def parse_date(cls, value):
        try:
            value = parser.isoparse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError(
                "Invalid date format. Should be provided as YYYY-MM-DD with optional Thh:mm:ss.sssZ") from None
        return value

class EnaExperimentModel(EnaBaseModel):
    description: Optional[str] = None
    study: Optional[EnaLinkingField] = None
    samples: Optional[list[EnaLinkingField]] = None
    designDescription: Optional[str] = None
    libraryDescriptor: Optional[EnaLibraryDescriptor] = None
    instrumentPlatform: Optional[EnaInstrumentPlatform] = None
    instrumentModel: Optional[EnaInstrumentModel] = None


class EnaRunModel(EnaBaseModel):
    experiment: EnaLinkingField
    instrumentPlatform: Optional[EnaInstrumentPlatform] = None
    instrumentModel: Optional[EnaInstrumentModel] = None
    files: list[EnaFile]

class EnaStudyModel(EnaBaseModel):
    description: Optional[str] = None

class EnaProjectModel(EnaBaseModel):
    description: Optional[str] = None

class EnaSubmissionModel(EnaBaseModel):
    submissionDate: Optional[str] = None
    actions: list[EnaAction]

    @field_validator('submissionDate')
    @classmethod
    def parse_date(cls, value):
        try:
            value = parser.isoparse(value).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            raise ValueError(
                "Invalid date format. Should be provided as YYYY-MM-DD with optional Thh:mm:ss.sssZ") from None
        return value