import os

file_path = "admin/admin-news-edit.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# ==========================================
# 1. Update CSS
# ==========================================
new_css = """
        /* Floating Toolbar V2 */
        .text-toolbar {
            position: fixed;
            background: white;
            border: 1px solid #e5e5e5;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            padding: 4px;
            z-index: 1000;
            display: none;
            align-items: center;
            gap: 2px;
            font-size: 14px;
        }

        .text-toolbar.active {
            display: flex;
            animation: fadeIn 0.1s ease-out;
        }

        .toolbar-btn {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            cursor: pointer;
            color: #374151;
            transition: background 0.1s;
            border: none;
            background: transparent;
        }

        .toolbar-btn:hover {
            background: #f3f4f6;
            color: black;
        }

        .toolbar-dropdown-trigger {
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
            color: #374151;
            font-weight: 500;
        }
        
        .toolbar-dropdown-trigger:hover {
            background: #f3f4f6;
        }

        .toolbar-separator {
            width: 1px;
            height: 20px;
            background: #e5e5e5;
            margin: 0 6px;
        }

        /* Dropdown Menu */
        .toolbar-dropdown-menu {
            position: absolute;
            top: 100%;
            left: 0;
            background: white;
            border: 1px solid #e5e5e5;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            padding: 4px;
            min-width: 160px;
            margin-top: 4px;
            display: none;
        }
        
        .toolbar-dropdown-menu.active {
            display: block;
        }

        .color-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }
        
        .color-item:hover {
            background: #f3f4f6;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
"""

# Find old CSS block
trigger_css = "/* Floating Toolbar */"
if trigger_css in content:
    start = content.find(trigger_css)
    end = content.find("</style>", start)
    if start != -1 and end != -1:
        content = content[:start] + new_css + content[end:]
        print("CSS Updated")
else:
    print("CSS anchor not found. Trying backup anchor.")
    # Fallback to appending if not found? No, better warn.

# ==========================================
# 2. Update Toolbar HTML
# ==========================================
new_toolbar = """
    <!-- Floating Text Toolbar V2 -->
    <div id="textToolbar" class="text-toolbar">
        <!-- Block Type Dropdown -->
        <div class="relative">
             <div class="toolbar-dropdown-trigger" onclick="toggleDropdown('blockTypeDropdown')">
                 <span>Text</span> <i data-lucide="chevron-down" class="w-3 h-3"></i>
             </div>
             <div id="blockTypeDropdown" class="toolbar-dropdown-menu">
                 <div class="color-item" onclick="setBlockType('paragraph')"><i data-lucide="type" class="w-4 h-4"></i> Text</div>
                 <div class="color-item" onclick="setBlockType('h1')"><i data-lucide="heading-1" class="w-4 h-4"></i> Heading 1</div>
                 <div class="color-item" onclick="setBlockType('h2')"><i data-lucide="heading-2" class="w-4 h-4"></i> Heading 2</div>
                 <div class="color-item" onclick="setBlockType('ul')"><i data-lucide="list" class="w-4 h-4"></i> Bullet List</div>
                 <div class="color-item" onclick="setBlockType('ol')"><i data-lucide="list-ordered" class="w-4 h-4"></i> Numbered List</div>
                 <div class="color-item" onclick="setBlockType('quote')"><i data-lucide="quote" class="w-4 h-4"></i> Quote</div>
                 <div class="color-item" onclick="setBlockType('code')"><i data-lucide="code" class="w-4 h-4"></i> Code</div>
             </div>
        </div>
        
        <div class="toolbar-separator"></div>

        <button class="toolbar-btn" onclick="formatText('bold')" title="Bold"><i data-lucide="bold" class="w-4 h-4"></i></button>
        <button class="toolbar-btn" onclick="formatText('italic')" title="Italic"><i data-lucide="italic" class="w-4 h-4"></i></button>
        <button class="toolbar-btn" onclick="formatText('underline')" title="Underline"><i data-lucide="underline" class="w-4 h-4"></i></button>
        <button class="toolbar-btn" onclick="formatText('strikethrough')" title="Strike"><i data-lucide="strikethrough" class="w-4 h-4"></i></button>
        <button class="toolbar-btn" onclick="formatText('code')" title="Code"><i data-lucide="code" class="w-4 h-4"></i></button>
        <button class="toolbar-btn" onclick="formatText('createLink')" title="Link"><i data-lucide="link" class="w-4 h-4"></i></button>
        
        <div class="toolbar-separator"></div>
        
        <!-- Color Dropdown -->
         <div class="relative">
             <div class="toolbar-dropdown-trigger" onclick="toggleDropdown('colorDropdown')">
                 <span class="text-lg">A</span> <i data-lucide="chevron-down" class="w-3 h-3"></i>
             </div>
             <div id="colorDropdown" class="toolbar-dropdown-menu" style="width: 200px; max-height: 300px; overflow-y: auto;">
                 <div class="p-2 text-xs font-bold text-gray-500">COLOR</div>
                 <div class="color-item" onclick="setColor('foreColor', 'black')"><div class="w-4 h-4 border rounded bg-black"></div> Default</div>
                 <div class="color-item" onclick="setColor('foreColor', '#9CA3AF')"><div class="w-4 h-4 border rounded bg-gray-400"></div> Gray</div>
                 <div class="color-item" onclick="setColor('foreColor', '#B45309')"><div class="w-4 h-4 border rounded bg-yellow-700"></div> Brown</div>
                 <div class="color-item" onclick="setColor('foreColor', '#EA580C')"><div class="w-4 h-4 border rounded bg-orange-600"></div> Orange</div>
                 <div class="color-item" onclick="setColor('foreColor', '#D97706')"><div class="w-4 h-4 border rounded bg-yellow-500"></div> Yellow</div>
                 <div class="color-item" onclick="setColor('foreColor', '#16A34A')"><div class="w-4 h-4 border rounded bg-green-600"></div> Green</div>
                 <div class="color-item" onclick="setColor('foreColor', '#2563EB')"><div class="w-4 h-4 border rounded bg-blue-600"></div> Blue</div>
                 <div class="color-item" onclick="setColor('foreColor', '#9333EA')"><div class="w-4 h-4 border rounded bg-purple-600"></div> Purple</div>
                 <div class="color-item" onclick="setColor('foreColor', '#DB2777')"><div class="w-4 h-4 border rounded bg-pink-600"></div> Pink</div>
                 <div class="color-item" onclick="setColor('foreColor', '#DC2626')"><div class="w-4 h-4 border rounded bg-red-600"></div> Red</div>
                 
                 <div class="p-2 text-xs font-bold text-gray-500 border-t mt-1">BACKGROUND</div>
                 <div class="color-item" onclick="setColor('hiliteColor', 'white')"><div class="w-4 h-4 border rounded bg-white"></div> Default</div>
                 <div class="color-item" onclick="setColor('hiliteColor', '#F3F4F6')"><div class="w-4 h-4 border rounded bg-gray-100"></div> Gray background</div>
                 <div class="color-item" onclick="setColor('hiliteColor', '#FEF3C7')"><div class="w-4 h-4 border rounded bg-yellow-100"></div> Yellow background</div>
                 <div class="color-item" onclick="setColor('hiliteColor', '#DCFCE7')"><div class="w-4 h-4 border rounded bg-green-100"></div> Green background</div>
                 <div class="color-item" onclick="setColor('hiliteColor', '#DBEAFE')"><div class="w-4 h-4 border rounded bg-blue-100"></div> Blue background</div>
                 <div class="color-item" onclick="setColor('hiliteColor', '#FEE2E2')"><div class="w-4 h-4 border rounded bg-red-100"></div> Red background</div>
             </div>
        </div>
    </div>
    
    <script>
    function toggleDropdown(id) {
        document.querySelectorAll('.toolbar-dropdown-menu').forEach(e => {
            if(e.id !== id) e.classList.remove('active');
        });
        document.getElementById(id).classList.toggle('active');
    }
    </script>
"""

if '<div id="textToolbar"' in content:
    start = content.find('<div id="textToolbar"')
    # Look for unique end marker
    end_marker = '<!-- Image Upload (hidden) -->'
    end = content.find(end_marker)
    if start != -1 and end != -1:
        content = content[:start] + new_toolbar + "\n    " + content[end:]
        print("Toolbar HTML Updated")
    else:
        print("Toolbar End marker not found")
else:
    print("Toolbar Start marker not found")


# ==========================================
# 3. Remove Legacy JS
# ==========================================
start_marker = "<script>lucide.createIcons();"
end_marker_str = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2">'

if start_marker in content:
    start = content.find(start_marker)
    end = content.find(end_marker_str)
    
    if start != -1 and end != -1:
        # Before removing, preserve the loadPost/action logic but using the NEW initEditorFeatures
        # Actually initEditorFeatures handles drag drop etc.
        # But we still need logic to LOAD EXISTING POST.
        # Check lines 1460-1477 in step 559.
        # We should keep the initialization of loadPost.
        
        legacy_script_replacement = """<script>
                        // Initialize Editor
                        document.addEventListener('DOMContentLoaded', async () => {
                            await checkAuth(); // Defined in header script? NO!
                            // checkAuth was defined IN THE BLOCK WE ARE REMOVING!
                            
                            // We need to keep checkAuth, loadPost, uploadImage, etc if they were in that block.
                            // Let's recover them?
                            
                            // OH NO. The block I'm removing contains EVERYTHING including `checkAuth`, `loadPost`, `uploadImage`.
                            // I MUST KEEP THEM.
                            // I only want to remove `initEditor`, `handleEditorKeydown`, `addBlock`, etc.
                            
                            // STRATEGY CHANGE: 
                            // Don't result to mass deletion if I'm not sure what's inside.
                            // Instead, I will let the new `notion-features.js` overwrite the functions if possible.
                            // OR I append `notion-features.js` at the END.
                            
                            // If `addBlock` is defined twice?
                            // The one loaded LAST wins (if using function declaration `function addBlock()`).
                            // `notion-features.js` is loaded at line 1486 (end of body).
                            // The inline script is before it? No, step 559: inline script is 1460.
                            // `notion-features.js` is 1486.
                            // So `notion-features.js` wins.
                            
                            // HOWEVER, `initEditor` is called inside the inline script. 
                            // It calls `addBlock` ... which will be the OLD ONE because `notion-features.js` hasn't loaded yet?
                            // Wait, `DOMContentLoaded` fires after all scripts load.
                            // So when `initEditor` runs inside `DOMContentLoaded`, `notion-features.js` functions SHOULD be ready.
                            
                            // BUT `initEditor` ITSELF is defined in the inline script.
                            // If I don't remove it, the OLD `initEditor` runs.
                            // And the OLD `initEditor` binds OLD event listeners.
                            
                            // So I MUST remove `initEditor`.
                            // But keep `checkAuth`, `loadPost`.
                        });
                        
                        // We will rely on notion-features.js to init features.
                        // But data loading?
        </script>"""
        
        # This is risky.
        # Better Strategy:
        # Just rename `initEditor` in the old script to `initEditor_Legacy`?
        # Use Python regex to rename: `function initEditor()` -> `function initEditor_Legacy()`
        # `function addBlock` -> `function addBlock_Legacy()`
        # `function showBlockMenuFor` -> ...
        
        # This effectively disables them without deleting needed helper functions like `checkAuth`.
        print("Renaming legacy functions to avoid conflict")
        content = content.replace("function initEditor()", "function initEditor_Legacy()")
        content = content.replace("function addBlock(", "function addBlock_Legacy(")
        content = content.replace("function showBlockMenuFor(", "function showBlockMenuFor_Legacy(")
        content = content.replace("function handleEditorKeydown(", "function handleEditorKeydown_Legacy(")
        
        # Also, in the `DOMContentLoaded` block, replace `initEditor()` call with `// initEditor() legacy disabled`
        content = content.replace("initEditor();", "// initEditor(); \\n initEditorFeatures(); // Call new init")
        
        print("Legacy JS disabled")

    else:
        print("Script block end not found")
else:
    print("Script block start not found")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
