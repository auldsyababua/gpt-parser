# Cleanup Checklist

After completing a task, please ensure:

1. **Remove temporary files from scratch/**
   - Any test scripts created during development
   - Temporary data files
   - Work-in-progress code that wasn't needed

2. **Verify file locations**
   - New parsers are in `parsers/`
   - External integrations are in `integrations/`
   - CLI tools are in `cli/`
   - No production code in `scratch/`

3. **Update CLAUDE.md if needed**
   - Document any new patterns discovered
   - Add any recurring issues to avoid

4. **Run tests**
   ```bash
   python -m pytest tests/
   ruff check .
   ```

5. **Check imports**
   - Ensure all imports use the new structure
   - No references to old `scripts/` paths