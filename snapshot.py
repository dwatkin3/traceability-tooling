import os
import sys

def generate_snapshot(root, output_file="snapshot.txt"):
    root = os.path.abspath(root)

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"FOLDER SNAPSHOT FOR: {root}\n")
        out.write("=====================================================\n\n")

        # 1) Folder Tree
        out.write("=== FOLDER TREE ===\n")
        for dirpath, dirnames, filenames in os.walk(root):
            # indentation based on depth
            level = dirpath.replace(root, "").count(os.sep)
            indent = " " * 4 * level
            out.write(f"{indent}{os.path.basename(dirpath)}/\n")

            file_indent = " " * 4 * (level + 1)
            for f in filenames:
                out.write(f"{file_indent}{f}\n")
        out.write("\n")

        # 2) File contents
        out.write("=== FILE CONTENTS ===\n")
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                out.write(f"\n----- FILE: {full_path} -----\n")
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        out.write(f.read())
                except:
                    out.write("[Skipped: binary or unreadable file]\n\n")

    print(f"Snapshot saved to {output_file}")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    generate_snapshot(folder)