#!/usr/bin/env python3
"""Regenerate Ssadassa.xcodeproj from the kit's working iOS project (scripts/round4/ios/MiniApp.xcodeproj).

Every *.swift under Ssadassa/ becomes a source of the Ssadassa target, with IDs derived from the path, so running
it again after adding or removing a file gives a stable project. Assets.xcassets (characters, icon) is a folder
reference and needs no listing. Run from anywhere:  python3 submissions/26510358/round-4/ios/gen_xcodeproj.py
"""
import hashlib
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
KIT = HERE.parents[3] / "scripts" / "round4" / "ios" / "MiniApp.xcodeproj" / "project.pbxproj"


def oid(s):
    return hashlib.md5(("ssadassa:" + s).encode()).hexdigest()[:24].upper()


def main():
    src = KIT.read_text()
    files = sorted(str(p.relative_to(HERE / "Ssadassa")) for p in (HERE / "Ssadassa").rglob("*.swift"))
    for fid, bid in [("DFA6013841C120544A49B10A", "6BE813A7514430BA9A756E25"),      # MiniAppApp.swift
                     ("C2D5606679541EC1B63F7E7A", "F772C489FF6ECE4CBF9F49C9"),      # LinkScreen.swift
                     ("C9B0ED4FA32BE007BC751F44", "B439ECF203294A63124E8016")]:     # AppScreen.swift
        src = "\n".join(line for line in src.split("\n") if fid not in line and bid not in line)
    for a, b in [("MiniApp.app", "Ssadassa.app"), ('"MiniApp"', '"Ssadassa"'), ("/* MiniApp */", "/* Ssadassa */"),
                 ("path = MiniApp;", "path = Ssadassa;"), ("name = MiniApp;", "name = Ssadassa;"),
                 ("productName = MiniApp;", "productName = Ssadassa;"),
                 ("INFOPLIST_FILE = MiniApp/Info.plist", "INFOPLIST_FILE = Ssadassa/Info.plist"),
                 ('INFOPLIST_KEY_CFBundleDisplayName = "Mini App"', 'INFOPLIST_KEY_CFBundleDisplayName = "Hermes Shop"'),
                 ("ai.ourolabs.agentmarket.miniapp", "kr.ac.seoultech.s26510358.ssadassa")]:
        src = src.replace(a, b)
    assert "MiniApp" not in src, [line for line in src.split("\n") if "MiniApp" in line][:3]
    name = lambda f: pathlib.Path(f).name
    src = src.replace("/* End PBXBuildFile section */", "".join(
        f"\t\t{oid('b' + f)} /* {name(f)} in Sources */ = {{isa = PBXBuildFile; fileRef = {oid('f' + f)} /* {name(f)} */; }};\n"
        for f in files) + "/* End PBXBuildFile section */")
    src = src.replace("/* End PBXFileReference section */", "".join(
        f"\t\t{oid('f' + f)} /* {name(f)} */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = {f}; sourceTree = \"<group>\"; }};\n"
        for f in files) + "/* End PBXFileReference section */")
    src = src.replace("\t\t\t\t32BB636196F91ED59D7A4919 /* Assets.xcassets */,\n", "".join(
        f"\t\t\t\t{oid('f' + f)} /* {name(f)} */,\n" for f in files) + "\t\t\t\t32BB636196F91ED59D7A4919 /* Assets.xcassets */,\n", 1)
    src, n = re.subn(r"(isa = PBXSourcesBuildPhase;\n\t\t\tbuildActionMask = 2147483647;\n\t\t\tfiles = \(\n)",
                     lambda m: m.group(1) + "".join(f"\t\t\t\t{oid('b' + f)} /* {name(f)} in Sources */,\n" for f in files), src)
    assert n == 1 and src.count("{") == src.count("}") and src.count("(") == src.count(")")
    out = HERE / "Ssadassa.xcodeproj"
    out.mkdir(exist_ok=True)
    (out / "project.pbxproj").write_text(src)
    print(f"[gen] {len(files)} Swift files -> {out.name}/project.pbxproj")


if __name__ == "__main__":
    main()
