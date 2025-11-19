# Build the final image using base image



FROM ghcr.io/acts-project/ubuntu2404:82

COPY --from=ghcr.io/opendatadetector/sw:dd4hep-git.a3fdbc4302494ee6dad3e3da460ec42b2b61c99f_master-e73pagfqbqsozbytbilxsxu6wkcshurl.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:lhapdfsets-6.5.5-t6ktxnwzogetazb5bmvloawvaw2pyftm.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:cmake-3.31.9-vmsz4xqd37d6sjqy4uqzufe6cmplqg7e.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:hepmc3-3.3.0-zngahz6y5b3bhmziveacllxwnj3ik7nc.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:python-3.14.0-xoadzjkbxlo4z5p6gblwwwncolizv5vw.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:intel-tbb-2022.0.0-jagwdffayxwrfzzafzr7ypd6fkxkktfo.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:madgraph5amc-3.5.9-nf6etm5ib6dhzxq7aq72ngvgxncvqxs2.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:acts-main-2zwkcnjyvd6z5fvskj3uqmhpm56xqbac.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:bzip2-1.0.8-i5faxwegiw2djbbobz4ojdmkyo5ocmbs.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:py-pip-25.1.1-szaamsnynbkjm2n3dmrat2mjxsnnhfzl.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:pythia8-8.313-ustf33bon6cdezi4vhkyc2mufordng7y.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:boost-1.88.0-khfxpfxyjn6rziupaw63rhiirpz73edw.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:geant4-11.3.2-tqvbidwktmdrdpvjxrrzir5edxp5viwj.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:py-pyyaml-6.0.3-efuw7agqw2cvglim2ccntmkorzjjl4ep.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:fastjet-3.5.0-wnmey5f7m4bwr4y3w7uh2wcx3jujwsx5.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:podio-1.3-36n3dexap6ipmpts63lob2amwfevfhvc.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:lz4-1.10.0-q3pw26ljukq2tnp2bev3t6rb63aww2ge.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:geomodel-6.19.0-wyeapjemy6aovg2tcuqkqxhdki4l6tjm.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:edm4hep-0.99.2-ysmdwxbetqkzfi3o4nfsronxjqglzr6r.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:nlohmann-json-3.11.3-xmbpenla74v2bxijkiv7jqzmocojf6gl.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:root-6.36.02-firjb4y4qcqzmdt4efkpsjm6fzkejsk5.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:py-pybind11-3.0.0-4roaqhxa7xpvkpitw7577heceya4rnvo.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:zstd-1.5.7-ilgps2ipdx6ofimdsk4ym52fxw3ngkex.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:eigen-3.4.0-2izrkvdgduqj44l2aizdq47amk3ja3ny.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:zlib-ng-2.2.4-lonviugvgv3f52d7zviy4jspoic5ynny.spack /spack /spack
COPY --from=ghcr.io/opendatadetector/sw:py-jinja2-3.1.6-r3a4huxi6b5nmq6xytnyrknp6dkqu7dz.spack /spack /spack





RUN <<EOT bash
set -eux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "\$ID" = "ubuntu" ]; then
    apt-get update
    apt-get install -y \\
      ninja-build \\
      ccache
    fi
fi
EOT

RUN curl -LsSf https://astral.sh/uv/0.9.10/install.sh | sh
ENV PATH=/root/.local/bin:$PATH

COPY docker/download_geant4_datasets.sh /usr/local/bin
COPY docker/download_geant4_datasets.py /usr/local/bin/_download_geant4_datasets.py

ENV CCACHE_DIR=/ccache
RUN mkdir /ccache

RUN <<EOT bash
set -eux
set -o pipefail

base_dir=$(dirname $(find /spack -type d -name "root-*"))

echo "BASE_DIR=\$base_dir" >> ~/.bashrc

mkdir /g4data
ln -sf /g4data \$base_dir/geant4-11.3.2-tqvbidwktmdrdpvjxrrzir5edxp5viwj/share/Geant4/data

EOT

RUN cat <<EOF >> ~/.bashrc

declare -a prefixes=(
  geomodel-6.19.0-wyeapjemy6aovg2tcuqkqxhdki4l6tjm py-scikit-build-core-0.11.5-7s5v7qliqtthxploa6ydt2vedkggjksm py-pybind11-3.0.0-4roaqhxa7xpvkpitw7577heceya4rnvo
  sed-4.9-2mfhea7gkuikgrfa4utzl725rrbaiaec grep-3.11-yjtvyjn3ffxthqcsivn6bghhxdeswkls go-bootstrap-1.22.12-7buseifnpfbpfokhi5msyovu5upskcxm
  bash-5.3-apwe4vw6ttxzd7pjku7r3k6cau6x4wcf go-1.25.3-bmj4da7xvnf27ntshrzpqxxotnf2bkbo eigen-3.4.0-2izrkvdgduqj44l2aizdq47amk3ja3ny
  acts-main-2zwkcnjyvd6z5fvskj3uqmhpm56xqbac popt-1.19-cfj2cngevktnymbhxna6dztz34tkzpht rsync-3.4.1-ou2bs6sayu5zha3lm3mqn45utoyvdmo7
  hepmc-2.06.11-z4j64e645be3xxwb27ybsgelmibbnd7a pythia8-8.313-ustf33bon6cdezi4vhkyc2mufordng7y py-six-1.17.0-ii5365xy6ic34j4mgfswhgnbla5oyl7q
  libtirpc-1.3.7-3xeptaongz7be5t7hds5dtqyedyexhjs gosam-contrib-2.0-2egny7wukwxrol7lmywrsebxp4nh5ngt fastjet-3.5.0-wnmey5f7m4bwr4y3w7uh2wcx3jujwsx5
  collier-1.2.8-i3npt2l7ufhpwqegeqnqysrd2abqefgw madgraph5amc-3.5.9-nf6etm5ib6dhzxq7aq72ngvgxncvqxs2 yaml-cpp-0.8.0-smzcf72irjxnofbvzs7uxgtptg54lyrw
  lhapdf-6.5.5-7jrxefaxo2byqzt4i5o3y3klyfxpk2wx lhapdfsets-6.5.5-t6ktxnwzogetazb5bmvloawvaw2pyftm py-pygments-2.19.2-bxen5u6dkg2lddvzrccewd6aidvqccls
  py-calver-2025.4.17-ylrldevcjbvlsw34ugqefxryf25emgip py-trove-classifiers-2025.9.11.17-eudrdyw3teqrtu2zl7fernk2mk3ghobl pcre2-10.44-spudpa2tejgm7wbrblu6rrkbgdn4gumd
  libxcrypt-4.4.38-exqcpv4npaused247kui5lpbita3hoze libedit-3.1-20240808-2ckrxmyiyiptmmaelz26dvv3gthp7jch bison-3.8.2-36wf2krlhjcrbyla7tceytbl4tsgtdxx
  krb5-1.21.3-4udzg42zmyrj3mpxa4gb2w5wm3xmo2cf openssh-9.9p1-ptp76a7l3ybiicbnunyi2ugmjcupa34y findutils-4.10.0-5ok5atq3s3zzanazaghtq7km3l5p4npm
  libtool-2.4.7-pxmoxa24u6ydhps7kuaohhzy72pfl4la libunistring-1.2-aqrt5tkygonsfbb4c6lf52cghhfl6g7l libidn2-2.3.7-4mi75gw6ljwr7pp7j6heqdzd2md26jtk
  py-setuptools-scm-8.2.1-oqwbowwmt66bqon2phlumaxccrzzvagv py-pluggy-1.6.0-ultztzhm45tjap54qvy2xi2h3xekr4yk py-pathspec-0.12.1-gfdp47igrlxwz72cowktfhsedazr4ves
  py-packaging-25.0-fuwuirkrkcwvkywqspvfqhqsb2r7jufc py-hatchling-1.27.0-2nu3y3ypamacnpvsoi4q65jpkzi5j64o py-hatch-vcs-0.5.0-q32qlmhagitkqftjuupdh5w7fjzu3ff3
  py-iniconfig-2.1.0-qe3a45bgjinnl4kwwtivvmcjoqmzkl54 py-pytest-8.4.1-gd4wd6x4uji2rivvhyqb33c4vjwewyfl re2c-3.1-fdvgmi54ifkazq5pc6ofqvbitlr2we42
  ninja-1.13.0-jqmwx7sr2o2dgp5vilf5tcl5th7pdmzp hepmc3-3.3.0-zngahz6y5b3bhmziveacllxwnj3ik7nc xerces-c-3.3.0-2qg5og3lbdqzrwcllq2ggufervbilxn2
  clhep-2.4.7.1-dxqkxtzub2zq2pnyjjd4h57dh5z6hjyl geant4-11.3.2-tqvbidwktmdrdpvjxrrzir5edxp5viwj xxhash-0.8.3-iyjfp2mwvkueryyovlzvyujeeashg3mg
  vdt-0.4.6-7dthgi7ob3uadbvdloifrgl3smjoxxwu rngstreams-1.0.1-wqqutnf76teoiwmlfhfqkbwgaai4dtjr unuran-1.11.0-smxe3l72hdbpgtwlrmpnonozqa7zznww
  pcre-8.45-vis2m7qa32trpgy52wqwtvtersi26yxc lz4-1.10.0-q3pw26ljukq2tnp2bev3t6rb63aww2ge libxpm-3.5.17-gd7kt7uy6szz7j23ud4fu7a2sbfcqhwj
  renderproto-0.11.1-5lwxvj4dauy57fvfoh7cjrxhayawdpgb libxrender-0.9.12-mb3ifjt7cq7spnzihfmro2u3qr3euq3u libxft-2.3.8-uoz3v7c72gjl3hcpowssmmxchltdnxjy
  libxext-1.3.6-fogs722balzf4dr35wj72ubwdaeuhgx2 xextproto-7.3.0-7mfgq36xsl6dd7ka5ulitrh4mcswh2xc xcb-proto-1.17.0-mvsnibwik3slgka5jhilcyr4yompf34d
  libxdmcp-1.1.5-jzy3djz6d3yqd6i2npf5y5phebkjjvz3 libxau-1.0.12-e45i6bfr6hofxggz7fmm3kvzklo2vaaz libpthread-stubs-0.5-hc7gl35u2ccgwbdb6dyxoe4yojelywuo
  libxcb-1.17.0-bafzlkk4wzdbigx42kq6kfmypipfltua kbproto-1.0.7-nmnvem5hy35fpeww5xfbt5t5gynvdvt6 inputproto-2.3.2-scov3xkjpvryh2qgt4j4765dlyzejkmq
  libx11-1.8.12-tlg3jqcqm6j7ownwb5rrtz6snncjtwwu libtiff-4.7.0-aqvxxefnszayguqochv5jh2tny6klx5r libsm-1.2.6-z4kdykjl4a7ciuy6bn7at77tsx5wph4f
  nasm-2.16.03-4sj2flmja7midso7wjzmougozlifn5gi libjpeg-turbo-3.0.4-zpdunsouta7g2fdlto3guyctp3qkoogp libice-1.1.2-olfbxc6y5vjt5nvznkdwbdwhkqqiictf
  libpciaccess-0.17-27wnoqhcq6ddljjmu5id2dk4ximmjtsx hwloc-2.12.2-mju6ykvu2y6cchzraafdgvtae2yxzwwb intel-tbb-2022.0.0-jagwdffayxwrfzzafzr7ypd6fkxkktfo
  gsl-2.8-xbvrehx2eorkxuxcdsvhq353uz5aahot giflib-5.2.2-4irvwjoyxlbw4qmizm4x3biilurjhrlo gperf-3.1-2z37xnqsahiejsk4rztumjz5h52y3pav
  mkfontscale-1.2.3-eqirx4g4j4trotxmtufphjwmeg3magyy mkfontdir-1.0.7-hdpd4ymi4ty6wzsjgjzdrrd3b3dn6ibb xtrans-1.6.0-l3pxo4xznouyvpyz3qmu33sc6n3audg5
  xproto-7.0.31-pcys5muw24t6hdpreymnpye4lpkjbqc3 libfontenc-1.1.8-gtbh36yam5rx2qqyxcy7ajlc3m4vbrk6 libpng-1.6.47-xphuane6s4ty74raxevqiclmegxspbxe
  freetype-2.14.1-4gowsg6tyqj5k6isdawv23iuzlvw4ce6 libxfont-1.5.4-x7yvxgltqtcxqjwqomnptsusvppansdd util-macros-1.20.1-uqjco4tqxenptueobq5qbkggieysrp5u
  fontsproto-2.1.3-itcrojsqe4ophnrcuzlsxb5stvztmlfs bdftopcf-1.1.1-hpzlfbs7qfswgsyibgvog2tz5b4dqrla automake-1.16.5-qfbj7cvuzjiyz742ejpbixwhi6pm6oz5
  libsigsegv-2.14-34yfszo5kr5sv7uv2gtk6iawgmq3a2pl m4-1.4.20-7kjs425ysrohj25brkglnaatsqfkow6j autoconf-2.72-o6t5glswozfhrmljfbt3y5so7mlyhyzy
  font-util-1.4.1-hckmgydyofzikttqmajjvknhgnhymklo fontconfig-2.15.0-md53rlngka5zd2ph2toq7vmcej7zrmm5 rapidjson-1.2.0-2024-08-16-tyvewffoqvnxskzdinbh6pedcrlokzpr
  davix-0.8.10-nstobttwdryg2pektwm4stvhysbkvj5d root-6.36.02-firjb4y4qcqzmdt4efkpsjm6fzkejsk5 py-tabulate-0.9.0-gdggiti72o5taewroboepua44bv2pu5y
  py-cython-3.1.3-w25tbbh6f5ak22b3tx3p3fpfqe5ejcxt libyaml-0.2.5-wmiy2oomo62u333ypvjceumyxbnjg66u py-pyyaml-6.0.3-efuw7agqw2cvglim2ccntmkorzjjl4ep
  py-markupsafe-3.0.2-fpi3izxfu57mkjnmysmgpxzvy7ua72s4 py-flit-core-3.12.0-hdbklqvmq6izojbwc5wupxdyqvyobndv py-jinja2-3.1.6-r3a4huxi6b5nmq6xytnyrknp6dkqu7dz
  py-wheel-0.45.1-nk2pwf665pdps26w4sfqgfsnniunurpn py-setuptools-80.9.0-smfop4bwhus6pms2wpdudoe3dzfroxdx python-venv-1.0-dpigcr2yxffze7jszye4nr22lzo27qrl
  util-linux-uuid-2.41-crwjxmjg2am3itp4yyo6gjwhtsfxu44f sqlite-3.50.4-hs6uhauwhkt5r5pnmur6scwyyfmsvqml libffi-3.5.2-tvo6sf27vbayb2l3vbubf5u2b6jce2ua
  pigz-2.8-byzet6awm26wh6nhtgsvcww5ktuaiml3 tar-1.35-xovrxqouxgv4ti57si7kwfrha454aqk6 libxml2-2.13.5-no4ivz4rvmihpt4zgeyi4nogpetsg5hc
  gettext-0.23.1-lgipyfn6yw5ldmyjn2bdhk4r3wr6e6tn libmd-1.1.0-5tnnek5jh5gib7ntbv3vrhi2r5lr3imv libbsd-0.12.2-zs5kjbfopags2i3zej2u2eivxzvake4l
  expat-2.7.3-5ujah7h6no3rfwgbpy74h6m4r4wkhmgt python-3.14.0-xoadzjkbxlo4z5p6gblwwwncolizv5vw py-pip-25.1.1-szaamsnynbkjm2n3dmrat2mjxsnnhfzl
  py-graphviz-0.20.3-ov3rlzomqwrirsx6zk3m5apaujltopaq fmt-12.1.0-kucngyqrqtff4yxs74jikxoec65uy3ri podio-1.3-36n3dexap6ipmpts63lob2amwfevfhvc
  nlohmann-json-3.11.3-xmbpenla74v2bxijkiv7jqzmocojf6gl edm4hep-0.99.2-ysmdwxbetqkzfi3o4nfsronxjqglzr6r zstd-1.5.7-ilgps2ipdx6ofimdsk4ym52fxw3ngkex
  xz-5.6.3-gxytvc6thol6errojvkrvyl5h64fbo5z boost-1.88.0-khfxpfxyjn6rziupaw63rhiirpz73edw zlib-ng-2.2.4-lonviugvgv3f52d7zviy4jspoic5ynny
  ncurses-6.5-20250705-xu5dz7ue747kjiyap3ter7gdnfbqfk56 readline-8.3-6c42wo67ciugxmjobv4w54sjdwyy453h gdbm-1.25-zutieiz2torpx2jgvnf4x2xajba25vkv
  bzip2-1.0.8-i5faxwegiw2djbbobz4ojdmkyo5ocmbs berkeley-db-18.1.40-ab3hpqcond454hfkp2sdwhksmkcyskvy perl-5.42.0-dpiqh4nv27azzkvuqhvylohslafudzuu
  ca-certificates-mozilla-2025-08-12-va7e2gqvyidd5nxe4lcivknwrd76bsxl openssl-3.6.0-fdljak7ydxzhhuzrfxogpnpvw7mcyhdy pkgconf-2.5.1-6d7cdecskiyarpwqrwhdufusmk3yzwkj
  libiconv-1.18-ivlelhrvehpmyeajyn34ta6ixy552iy5 diffutils-3.12-ixkzl33tikng2gxntompfiiv2pdm5t7l nghttp2-1.67.1-tzahjugxwl66wswd252vgniuj6wqt7kz
  gmake-4.4.1-h6ce6lyjisykmc3u5s6mek32thio7pin glibc-2.39-4bfivdkeg4jj64esmnemhojxf5wlw2km gcc-runtime-13.3.0-3eqru2mivrnphgr7msxclitni6o5gd6w
  gcc-13.3.0-uwfdr2q5yjm74qe7rxeukihjupvhft6q curl-8.15.0-lu3p6row7g5z3foiplictzrfkaxkuv6s compiler-wrapper-1.0-cpbsuow6nma4ib5tcxdpqkl3m2dkxher
  cmake-3.31.9-vmsz4xqd37d6sjqy4uqzufe6cmplqg7e assimp-6.0.2-x3mzng6d54otprrgnm6pa5khg5hiyd2b dd4hep-git.a3fdbc4302494ee6dad3e3da460ec42b2b61c99f=master-e73pagfqbqsozbytbilxsxu6wkcshurl
)

# Configure \$CMAKE_PREFIX_PATH
for p in "\${prefixes[@]}"; do
    CMAKE_PREFIX_PATH="\$BASE_DIR/\$p\${CMAKE_PREFIX_PATH:+:\${CMAKE_PREFIX_PATH}}"
done
export CMAKE_PREFIX_PATH

# CLHEP has a special location
export CMAKE_PREFIX_PATH=\$BASE_DIR/clhep-2.4.7.1-dxqkxtzub2zq2pnyjjd4h57dh5z6hjyl/lib/CLHEP-2.4.7.1:\$CMAKE_PREFIX_PATH

# Configure \$PATH Variable
for p in "\${prefixes[@]}"; do
    PATH="\$BASE_DIR/\$p/bin\${PATH:+:\${PATH}}"
done
export PATH

cat /etc/motd

EOF



RUN cat <<EOF >> /etc/motd
=============== ACTS development image with dependencies ===============
- Clone repository: 
    git clone https://github.com/acts-project/acts.git --recursive
- Configure: 
    cmake -S acts -B build -GNinja --preset dev \\
      -DACTS_BUILD_UNITTESTS=OFF -DACTS_BUILD_INTEGRATIONTESTS=OFF
- Build:
    cmake --build build
- Run:
    source build/this_acts_withdeps.sh
    acts/Examples/Scripts/Python/full_chain_odd.py -n1
========================================================================
EOF

ENTRYPOINT ["/bin/bash"]