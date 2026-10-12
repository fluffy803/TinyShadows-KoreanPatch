init python:

    def _tlgen_command():
        """
        Like the built-in `translate` command, but generates dialogue
        translations straight from the loaded (compiled) script instead of
        requiring loose .rpy sources on disk.
        """

        import renpy.translation.generation as g

        ap = renpy.arguments.ArgumentParser(
            description="Generate dialogue translations from compiled scripts.")
        ap.add_argument("language", help="The language to generate translations for.")
        ap.add_argument("--list", dest="list_only", action="store_true",
                        help="Only list the script files that would be processed.")
        args = ap.parse_args()

        translator = renpy.game.script.translator
        filenames = sorted(translator.file_translates.keys())

        print("=== file_translates keys: %d ===" % len(filenames))
        for fn in filenames:
            print("%6d  %s" % (len(translator.file_translates[fn]), fn))

        if args.list_only:
            return False

        g.todo = True

        for fn in filenames:
            g.write_translates(fn, args.language, g.null_filter)

        g.close_tl_files()

        print("=== done ===")
        return False

    renpy.arguments.register_command("tlgen", _tlgen_command)
