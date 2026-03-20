# tests/test_oto_file.py
"""
Testes para o módulo oto_file.
"""

import pytest
from pathlib import Path


class TestOtoFile:
    """Testes para a classe OtoFile."""
    
    def test_import(self):
        """Verifica se o módulo pode ser importado."""
        from copaiba import OtoFile
        assert OtoFile is not None
    
    def test_load_oto(self, temp_oto_file):
        """Testa carregamento de arquivo oto.ini."""
        from copaiba import OtoFile
        
        oto = OtoFile()
        oto.load(temp_oto_file, "utf-8")
        
        assert len(oto.entries) == 5
    
    def test_entry_properties(self, temp_oto_file):
        """Testa propriedades das entradas."""
        from copaiba import OtoFile
        
        oto = OtoFile()
        oto.load(temp_oto_file, "utf-8")
        
        # Primeira entrada: a.wav=a,0,100,50,30,-100
        entry = oto.entries[0]
        assert entry.alias == "a"
        assert entry.offset == 0
        assert entry.consonant == 100
        assert entry.cutoff == 50
        assert entry.preutter == 30
        assert entry.overlap == -100
    
    def test_save_oto(self, temp_dir, temp_oto_file):
        """Testa salvamento de arquivo oto.ini."""
        from copaiba import OtoFile
        
        oto = OtoFile()
        oto.load(temp_oto_file, "utf-8")
        
        # Salvar em novo arquivo
        new_path = temp_dir / "oto_new.ini"
        oto.save(new_path, "utf-8")
        
        assert new_path.exists()
        
        # Recarregar e verificar
        oto2 = OtoFile()
        oto2.load(new_path, "utf-8")
        assert len(oto2.entries) == 5
