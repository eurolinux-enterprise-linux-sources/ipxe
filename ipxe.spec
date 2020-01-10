
# Resulting binary formats we want from iPXE
%global formats rom

# PCI IDs (vendor,product) of the ROMS we want for QEMU
#
#    pcnet32: 0x1022 0x2000
#   ne2k_pci: 0x10ec 0x8029
#      e1000: 0x8086 0x100e
#    rtl8139: 0x10ec 0x8139
# virtio-net: 0x1af4 0x1000
%global qemuroms 10222000 10ec8029 8086100e 10ec8139 1af41000

# We only build the ROMs if on an x86 build host. The resulting
# binary RPM will be noarch, so other archs will still be able
# to use the binary ROMs.
#
# We do cross-compilation for 32->64-bit, but not for other arches
# because EDK II does not support big-endian hosts.
%global buildarches x86_64

# debugging firmwares does not goes the same way as a normal program.
# moreover, all architectures providing debuginfo for a single noarch
# package is currently clashing in koji, so don't bother.
%global debug_package %{nil}

# Upstream don't do "releases" :-( So we're going to use the date
# as the version, and a GIT hash as the release. Generate new GIT
# snapshots using the folowing commands:
#
# $ hash=`git log -1 --format='%h'`
# $ date=`date '+%Y%m%d'`
# $ git archive --output ipxe-${date}-git${hash}.tar.gz --prefix ipxe-${date}-git${hash}/ ${hash}
#
# And then change these two:

%global date 20130517
%global hash c4bce43

Name:    ipxe
Version: %{date}
Release: 8.git%{hash}%{?dist}.1
Summary: A network boot loader

Group:   System Environment/Base
License: GPLv2 and BSD
URL:     http://ipxe.org/

Source0: %{name}-%{version}-git%{hash}.tar.gz
Source1: USAGE
# Remove 2 second startup wait. This patch is not intended to
# go upstream. Modifying the general config header file is the
# intended means for downstream customization.
Patch1: %{name}-banner-timeout.patch
# GCC >= 4.8 doesn't like the use of 'ebp' in asm
# https://bugzilla.redhat.com/show_bug.cgi?id=914091
Patch2: %{name}-asm.patch
# For bz#1062644 - pxe boot fails if next-server details come from a different dhcp server
Patch3: ipxe-Use-next-server-from-filename-s-settings-block.patch
# For bz#1031518 - iPXE does not honor specified boot device
Patch4: ipxe-Enable-infrastructure-to-specify-an-autoboot-device-.patch
# For bz#1031518 - iPXE does not honor specified boot device
Patch5: ipxe-Allow-prefix-to-specify-a-PCI-autoboot-device-locati.patch
# For bz#1031518 - iPXE does not honor specified boot device
Patch6: ipxe-Store-boot-bus-dev.fn-address-as-autoboot-device-loc.patch
# For bz#1031518 - iPXE does not honor specified boot device
Patch7: ipxe-Ignore-PCI-autoboot-device-location-if-set-to-00-00..patch
# For bz#857123 - Guests never get an iPXE prompt
Patch8: ipxe-Revert-Remove-2-second-startup-wait.patch
# For bz#857123 - Guests never get an iPXE prompt
Patch9: ipxe-Allow-ROM-banner-timeout-to-be-configured-independen.patch
# For bz#857123 - Guests never get an iPXE prompt
Patch10: ipxe-Customize-ROM-banner-timeout.patch
# For bz#1084561 - RFE: ship UEFI drivers for ipxe in RHEL-7.y
Patch11: ipxe-import-EfiRom-from-edk2-BaseTools-RHEL-only.patch
# For bz#1084561 - RFE: ship UEFI drivers for ipxe in RHEL-7.y
Patch12: ipxe-add-custom-Makefile-for-EfiRom-RHEL-only.patch
# For bz#1196352 - [RFE] option to increase gpxe retry timeout
Patch13: ipxe-Extract-timing-parameters-out-to-config-dhcp.h.patch
# For bz#1196352 - [RFE] option to increase gpxe retry timeout
Patch14: ipxe-Use-spec-compliant-timeouts.patch

%ifarch %{buildarches}
BuildRequires: perl
BuildRequires: syslinux
BuildRequires: mtools
BuildRequires: mkisofs
BuildRequires: binutils-devel

Obsoletes: gpxe <= 1.0.1

%package bootimgs
Summary: Network boot loader images in bootable USB, CD, floppy and GRUB formats
Group:   Development/Tools
BuildArch: noarch
Obsoletes: gpxe-bootimgs <= 1.0.1

%package roms
Summary: Network boot loader roms in .rom format
Group:  Development/Tools
Requires: %{name}-roms-qemu = %{version}-%{release}
BuildArch: noarch
Obsoletes: gpxe-roms <= 1.0.1

%package roms-qemu
Summary: Network boot loader roms supported by QEMU, .rom format
Group:  Development/Tools
BuildArch: noarch
Obsoletes: gpxe-roms-qemu <= 1.0.1

%description bootimgs
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

This package contains the iPXE boot images in USB, CD, floppy, and PXE
UNDI formats.

%description roms
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

This package contains the iPXE roms in .rom format.


%description roms-qemu
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

This package contains the iPXE ROMs for devices emulated by QEMU, in
.rom format.
%endif

%description
iPXE is an open source network bootloader. It provides a direct
replacement for proprietary PXE ROMs, with many extra features such as
DNS, HTTP, iSCSI, etc.

%prep
%setup -q -n %{name}-%{version}-git%{hash}
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch9 -p1
%patch10 -p1
%patch11 -p1
%patch12 -p1
%patch13 -p1
%patch14 -p1
cp -a %{SOURCE1} .

%build
%ifarch %{buildarches}
# The src/Makefile.housekeeping relies on .git/index existing
# but since we pass GITVERSION= to make, we don't actally need
# it to be the real deal, so just touch it to let the build pass
mkdir .git
touch .git/index

ISOLINUX_BIN=/usr/share/syslinux/isolinux.bin
cd src
# ath9k drivers are too big for an Option ROM
rm -rf drivers/net/ath/ath9k

#make %{?_smp_mflags} bin/undionly.kpxe bin/ipxe.{dsk,iso,usb,lkrn} allroms \
make bin/undionly.kpxe bin/ipxe.{dsk,iso,usb,lkrn} allroms \
                   ISOLINUX_BIN=${ISOLINUX_BIN} NO_WERROR=1 V=1 \
		   GITVERSION=%{hash}

# build EfiRom
cd ../EfiRom
make %{?_smp_mflags}
cd ../src

# build roms with efi support for qemu
for rom in %qemuroms; do
  make NO_WERROR=1 V=1 GITVERSION=%{hash} bin/${rom}.rom
  make NO_WERROR=1 V=1 GITVERSION=%{hash} bin-x86_64-efi/${rom}.efidrv
  vid="0x${rom%%????}"
  did="0x${rom#????}"
  ../EfiRom/EfiRom -f "$vid" -i "$did" --pci23 \
                   -b  bin/${rom}.rom \
                   -ec bin-x86_64-efi/${rom}.efidrv \
                   -o  bin/${rom}.combined.rom
  ../EfiRom/EfiRom -d  bin/${rom}.combined.rom
  mv bin/${rom}.combined.rom bin/${rom}.rom
done

%endif

%install
%ifarch %{buildarches}
mkdir -p %{buildroot}/%{_datadir}/%{name}/
pushd src/bin/

cp -a undionly.kpxe ipxe.{iso,usb,dsk,lkrn} %{buildroot}/%{_datadir}/%{name}/

for fmt in %{formats};do
 for img in *.${fmt};do
      if [ -e $img ]; then
   cat $img /dev/zero | dd bs=256k count=1 of=$img.tmp iflag=fullblock
   install -D -p -m 0644 $img.tmp %{buildroot}/%{_datadir}/%{name}/$img
   rm $img.tmp
   echo %{_datadir}/%{name}/$img >> ../../${fmt}.list
  fi
 done
done
popd

# the roms supported by qemu will be packaged separatedly
# remove from the main rom list and add them to qemu.list
for fmt in rom ;do
 for rom in %{qemuroms} ; do
  sed -i -e "/\/${rom}.${fmt}/d" ${fmt}.list
  echo %{_datadir}/%{name}/${rom}.${fmt} >> qemu.${fmt}.list
 done
done
%endif

%ifarch %{buildarches}
%files bootimgs
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/ipxe.iso
%{_datadir}/%{name}/ipxe.usb
%{_datadir}/%{name}/ipxe.dsk
%{_datadir}/%{name}/ipxe.lkrn
%{_datadir}/%{name}/undionly.kpxe
%doc COPYING COPYRIGHTS USAGE

%files roms -f rom.list
%dir %{_datadir}/%{name}
%doc COPYING COPYRIGHTS

%files roms-qemu -f qemu.rom.list
%dir %{_datadir}/%{name}
%doc COPYING COPYRIGHTS
%endif

%changelog
* Tue Jan 26 2016 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-8.gitc4bce43.el7_2.1
- Rebuild for preventing conflicts [bz#1301855]

* Wed May 06 2015 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-7.gitc4bce43.el7
- ipxe-Extract-timing-parameters-out-to-config-dhcp.h.patch [bz#1196352]
- ipxe-Use-spec-compliant-timeouts.patch [bz#1196352]
- Resolves: bz#1196352
  ([RFE] option to increase gpxe retry timeout)

* Mon Sep 15 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-6.gitc4bce43.el7
- ipxe-import-EfiRom-from-edk2-BaseTools-RHEL-only.patch [bz#1084561]
- ipxe-add-custom-Makefile-for-EfiRom-RHEL-only.patch [bz#1084561]
- ipxe-redhat-delete-useless-editor-backup-of-spec.template.patch [bz#1084561]
- ipxe-redhat-build-and-install-combined-legacy-UEFI-roms-f.patch [bz#1084561]
- Resolves: bz#1084561
  (RFE: ship UEFI drivers for ipxe in RHEL-7.y)

* Wed Mar 05 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-5.gitc4bce43.el7
- ipxe-Enable-infrastructure-to-specify-an-autoboot-device-.patch [bz#1031518]
- ipxe-Allow-prefix-to-specify-a-PCI-autoboot-device-locati.patch [bz#1031518]
- ipxe-Store-boot-bus-dev.fn-address-as-autoboot-device-loc.patch [bz#1031518]
- ipxe-Ignore-PCI-autoboot-device-location-if-set-to-00-00..patch [bz#1031518]
- ipxe-Revert-Remove-2-second-startup-wait.patch [bz#857123]
- ipxe-Allow-ROM-banner-timeout-to-be-configured-independen.patch [bz#857123]
- ipxe-Customize-ROM-banner-timeout.patch [bz#857123]
- Resolves: bz#1031518
  (iPXE does not honor specified boot device)
- Resolves: bz#857123
  (Guests never get an iPXE prompt)

* Tue Feb 11 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-4.gitc4bce43
- ipxe-Use-next-server-from-filename-s-settings-block.patch [bz#1062644]
- Resolves: bz#1062644
  (pxe boot fails if next-server details come from a different dhcp server)

* Thu Jan 15 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-3.gitc4bce43
- pad ROMs to 256k (rhbz #1038630)
- Resolves: rhbz# 1038630

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 20130517-2.gitc4bce43
- Mass rebuild 2013-12-27

* Fri May 17 2013 Daniel P. Berrange <berrange@redhat.com> - 20130517-1.gitc4bce43
- Update to latest upstream snapshot

* Fri May 17 2013 Daniel P. Berrange <berrange@redhat.com> - 20130103-3.git717279a
- Fix build with GCC 4.8 (rhbz #914091)

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 20130103-2.git717279a
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Jan  3 2013 Daniel P. Berrange <berrange@redhat.com> - 20130103-1.git717279a
- Updated to latest GIT snapshot

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 20120328-2.gitaac9718
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Mar 28 2012 Daniel P. Berrange <berrange@redhat.com> - 20120328-1.gitaac9718
- Update to newer upstream

* Fri Mar 23 2012 Daniel P. Berrange <berrange@redhat.com> - 20120319-3.git0b2c788
- Remove more defattr statements

* Tue Mar 20 2012 Daniel P. Berrange <berrange@redhat.com> - 20120319-2.git0b2c788
- Remove BuildRoot & rm -rf of it in install/clean sections
- Remove defattr in file section
- Switch to use global, instead of define for macros
- Add note about Patch1 not going upstream
- Split BRs across lines for easier readability

* Mon Feb 27 2012 Daniel P. Berrange <berrange@redhat.com> - 20120319-1.git0b2c788
- Initial package based on gPXE

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Feb 21 2011 Matt Domsch <mdomsch@fedoraproject.org> - 1.0.1-4
- don't use -Werror, it flags a failure that is not a failure for gPXE

* Mon Feb 21 2011 Matt Domsch <mdomsch@fedoraproject.org> - 1.0.1-3
- Fix virtio-net ethernet frame length (patch by cra), fixes BZ678789

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Aug  5 2010 Matt Domsch <mdomsch@fedoraproject.org> - 1.0.1-1
- New drivers: Intel e1000, e1000e, igb, EFI snpnet, JMicron jme,
  Neterion X3100, vxge, pcnet32.
- Bug fixes and improvements to drivers, wireless, DHCP, iSCSI,
  COMBOOT, and EFI.
* Tue Feb  2 2010 Matt Domsch <mdomsch@fedoraproject.org> - 1.0.0-1
- bugfix release, also adds wireless card support
- bnx2 builds again
- drop our one patch

* Tue Oct 27 2009 Matt Domsch <mdomsch@fedoraproject.org> - 0.9.9-1
- new upstream version 0.9.9
-- plus patches from git up to 20090818 which fix build errors and
   other release-critical bugs.
-- 0.9.9: added Attansic L1E and sis190/191 ethernet drivers.  Fixes
   and updates to e1000 and 3c90x drivers.
-- 0.9.8: new commands: time, sleep, md5sum, sha1sum. 802.11 wireless
   support with Realtek 8180/8185 and non-802.11n Atheros drivers.
   New Marvell Yukon-II gigabet Ethernet driver.  HTTP redirection
   support.  SYSLINUX floppy image type (.sdsk) with usable file
   system.  Rewrites, fixes, and updates to 3c90x, forcedeth, pcnet32,
   e1000, and hermon drivers.

* Mon Oct  5 2009 Matt Domsch <mdomsch@fedoraproject.org> - 0.9.7-6
- move rtl8029 from -roms to -roms-qemu for qemu ne2k_pci NIC (BZ 526776)

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.7-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue May 19 2009 Matt Domsch <mdomsch@fedoraproject.org> - 0.9.7-4
- add undionly.kpxe to -bootimgs

* Tue May 12 2009 Matt Domsch <mdomsch@fedoraproject.org> - 0.9.7-3
- handle isolinux changing paths

* Sat May  9 2009 Matt Domsch <mdomsch@fedoraproject.org> - 0.9.7-2
- add dist tag

* Thu Mar 26 2009 Matt Domsch <mdomsch@fedoraproject.org> - 0.9.7-1
- Initial release based on etherboot spec
