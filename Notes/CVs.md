https://imagine.gsfc.nasa.gov/science/objects/cataclysmic_variables.html
https://web.archive.org/web/20080226032415/http://home.mindspring.com/~mikesimonsen/cvnet/id1.html
http://www.mssl.ucl.ac.uk/www_astro/gal/cv_beginners.html
https://heasarc.gsfc.nasa.gov/docs/objects/cvs/cvstext.html

# Astronomers Telegram
Looking for novae/CVs confused with other things.

```python
%run CVfncs
get_cvs_from_at()
```

__I got myself blocked, probably for suspected DNS.___


# ASAS-SN:
<!-- fs asassn -->
[web UI](https://asas-sn.osu.edu/variables)
    - _2057 CVs_ + subtypes (paper 2 says they did not classify these, just kept VSX classification)

[paper 1](https://arxiv.org/pdf/1803.01001.pdf)
[paper 2](https://arxiv.org/pdf/1809.07329.pdf)
[paper 3](https://arxiv.org/pdf/1901.00009.pdf)

<!-- fe asassn -->


# OGLE:
<!-- fs ogle -->
[web UI](http://ogle.astrouw.edu.pl/)
    - 5 'recurrent and symbiotic novae'
        - On-line Data -> ogle4/ -> NOVAE/
    - optical counterparts to Chandra X-ray sources in galactic bulge (unlabelled)
        - On-line Data -> ogle4/ -> XRAY-GBS/
    - 5 labelled as 'CV'
        - On-line Data -> ogle4/ -> short_period_ecl/
    - XROM (real time system) optical counterparts of x-ray binaries (no readme, seems like dirs/files on individual stars)
        - On-line Data -> ogle4/ -> xrom/

[OGLE-IV paper](http://acta.astrouw.edu.pl/Vol65/n1/pdf/pap_65_1_1.pdf)
    - survey design, photometric bands, description of real time systems

[CVOM: OGLE-IV REAL TIME MONITORING OF CATACLYSMIC VARIABLES](http://ogle.astrouw.edu.pl/ogle4/cvom/cvom.html)
    - ~50 on the current list

[Atlas of Variable Stars Lightcurves](http://ogle.astrouw.edu.pl/atlas/)
    - link to CVs is blank
    - "we also show _very rarely seen behaviors_, sometimes detected for the first time in the OGLE data"

*[One Thousand New Dwarf Novae from the OGLE Survey](http://ogle.astrouw.edu.pl/ogle4/cvom/cvom.html)*
    - [FTP](ftp://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/CV/)

*[CATALOG OF 93 NOVA LIGHT CURVES: CLASSIFICATION AND PROPERTIES](Mendeley)*
    - defines 7 classes based on lightcurve shapes
    - data mostly from AAVSO
    - [online article](https://iopscience.iop.org/article/10.1088/0004-6256/140/1/34#aj343738t2)
    - [Table 2 full version](https://iopscience.iop.org/1538-3881/140/1/34/suppdata/aj343738t2_mrt.txt)

## OCVS (catalog of variable stars)
[paper](http://acta.astrouw.edu.pl/Vol66/n4/pdf/pap_66_4_1.pdf)
[web UI](http://ogledb.astrouw.edu.pl/~ogle/OCVS/)
[FTP](ftp://ftp.astrouw.edu.pl/ogle/ogle4/OCVS/)
    - Blue Large-Amplitude Pulsators: a new class of variables
    - CVs (repo for One Thousand New Dwarf Novae, see above)
    - Misclassified Cepheids in various surveys
    - OGLE variables in:
        - entire Galaxy. also broken out by bulge, disk
        - LMC & SMC
        - M54 and Sagittarius Dwarf Spheroidal Galaxy
    - OGLE list of Galactic classical Cepheids (all surveys)
    * in blg directory:
        ```
        cols = ['id','subtype','ra','dec','4id','3id','2id','oid']
        df = pd.read_csv('ident.dat', names=cols, sep='\s+')
        df.groupby('subtype').size()                                              
        Out[18]:
        subtype
        C       86560
        CV         18
        ELL     25405
        NC     338615
        ```


<!-- fe ogle -->
