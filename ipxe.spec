
# Resulting binary formats we want from iPXE
%global formats rom

# PCI IDs (vendor,product) of the ROMS we want for QEMU
#
#    pcnet32: 0x1022 0x2000
#   ne2k_pci: 0x10ec 0x8029
#      e1000: 0x8086 0x100e
#    rtl8139: 0x10ec 0x8139
# virtio-net: 0x1af4 0x1000
#     e1000e: 0x8086 0x10d3
%global qemuroms 10222000 10ec8029 8086100e 10ec8139 1af41000 808610d3

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

%global date 20170123
%global hash 4e85b27

Name:    ipxe
Version: %{date}
Release: 1.git%{hash}%{?dist}.1
Summary: A network boot loader

Group:   System Environment/Base
License: GPLv2 and BSD
URL:     http://ipxe.org/

Source0: %{name}-%{date}-git%{hash}.tar.gz
Source1: USAGE

Patch1: 0001-Add-redhat-directory.patch
Patch2: 0002-import-EfiRom-from-edk2-BaseTools-RHEL-only.patch
Patch3: 0003-add-custom-Makefile-for-EfiRom-RHEL-only.patch
Patch4: 0005-Use-spec-compliant-timeouts.patch
Patch5: 0008-Enable-IPv6-protocol-in-non-QEMU-builds.patch
Patch6: 0009-Strip-802.1Q-VLAN-0-priority-tags.patch
# For bz#1481180 - iommu platform support for ipxe [rhel-7.4.z]
Patch7: ipxe-Support-VIRTIO_NET_F_IOMMU_PLATFORM.patch

%ifarch %{buildarches}
BuildRequires: perl
BuildRequires: syslinux
BuildRequires: mtools
BuildRequires: mkisofs
BuildRequires: binutils-devel
BuildRequires: xz-devel

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
%setup -q -n %{name}-%{hash}
cp -a %{SOURCE1} .

patch_command="patch -p1 -s"

%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1

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

make bin-x86_64-efi/ipxe.efi \
     NO_WERROR=1 V=1 GITVERSION=%{hash}

# build EfiRom
cd ../EfiRom
make %{?_smp_mflags}
cd ../src

# build roms with efi support for qemu
for rom in %qemuroms; do
  make NO_WERROR=1 V=1 GITVERSION=%{hash} CONFIG=qemu \
       bin/${rom}.rom bin-x86_64-efi/${rom}.efidrv
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

pushd src

cp -a bin/undionly.kpxe bin/ipxe.{iso,usb,dsk,lkrn} bin-x86_64-efi/ipxe.efi \
   %{buildroot}/%{_datadir}/%{name}/

cd bin
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
%{_datadir}/%{name}/ipxe.efi
%{_datadir}/%{name}/undionly.kpxe
%doc COPYING COPYING.GPLv2 USAGE

%files roms -f rom.list
%dir %{_datadir}/%{name}
%doc COPYING COPYING.GPLv2

%files roms-qemu -f qemu.rom.list
%dir %{_datadir}/%{name}
%doc COPYING COPYING.GPLv2
%endif

%changelog
* Thu Aug 17 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20170123-1.git4e85b27.el7_4.1
- ipxe-Support-VIRTIO_NET_F_IOMMU_PLATFORM.patch [bz#1481180]
- Resolves: bz#1481180
  (iommu platform support for ipxe [rhel-7.4.z])

* Fri Mar 10 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20170123-1.git4e85b27.el7
- Rebase to commit 4e85b27 [bz#1413781]
- Resolves: bz#1413781
  (Rebase ipxe for RHEL-7.4)

* Thu Sep 01 2016 Miroslav Rezanina <mrezanin@redhat.com> - 20160127-5.git6366fa7a.el7
- ipxe-Strip-802.1Q-VLAN-0-priority-tags.patch [bz#1316329]
- Resolves: bz#1316329
  ([RFE] Properly Handle 8021.Q VID 0 Frames, as new vlan model in linux kernel does.)

* Tue Aug 02 2016 Miroslav Rezanina <mrezanin@redhat.com> - 20160127-4.git6366fa7a.el7
- ipxe-Send-TCP-keepalives-on-idle-established-connections.patch [bz#1322056]
- ipxe-enable-e1000e-rom.patch [bz#1361534]
- Resolves: bz#1322056
  (ipxe freeze during HTTP download with last RPM)
- Resolves: bz#1361534
  (RFE: Integrate e1000e implementation in downstream QEMU)

* Fri Jul 15 2016 Miroslav Rezanina <mrezanin@redhat.com> - 20160127-3.git6366fa7a.el7
- ipxe-Add-pci_find_next_capability.patch [bz#1242850]
- ipxe-Add-virtio-1.0-constants-and-data-structures.patch [bz#1242850]
- ipxe-Add-virtio-1.0-PCI-support.patch [bz#1242850]
- ipxe-Add-virtio-net-1.0-support.patch [bz#1242850]
- ipxe-Renumber-virtio_pci_region-flags.patch [bz#1242850]
- ipxe-Fix-virtio-pci-logging.patch [bz#1242850]
- Resolves: bz#1242850
  (Ipxe can not recognize "network device" when enable virtio-1 of virtio-net-pci)

* Tue Jul 12 2016 Miroslav Rezanina <mrezanin@redhat.com> - 20160127-2.git6366fa7a.el7
- ipxe-Enable-IPv6-protocol-in-non-QEMU-builds.patch [bz#1350167]
- Resolves: bz#1350167
  (ipxe: enable IPV6)

* Wed Mar 09 2016 Miroslav Rezanina <mrezanin@redhat.com> - 20160127-1.git6366fa7a.el7
- Rebase to 6366fa7a
- Resolves: bz#1297853

* Mon Sep 15 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-6.gitc4bce43.el7
- ipxe-import-EfiRom-from-edk2-BaseTools-RHEL-only.patch [bz#1084561]
- ipxe-add-custom-Makefile-for-EfiRom-RHEL-only.patch [bz#1084561]
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

* Wed Jan 15 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20130517-3.gitc4bce43
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
