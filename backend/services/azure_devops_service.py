import os
import base64
import httpx
from typing import Optional, List, Dict
import json
import logging

logger = logging.getLogger(__name__)

class AzureDevOpsService:
    def __init__(self):
        self.org_url = os.getenv("AZURE_DEVOPS_ORG")
        self.project = os.getenv("AZURE_DEVOPS_PROJECT")
        self.pat = os.getenv("AZURE_DEVOPS_PAT")
        # Work item type can be configured, defaults to common types
        # Common types: "User Story", "Product Backlog Item", "Issue", "Task", "Bug"
        self.work_item_type = os.getenv("AZURE_DEVOPS_WORK_ITEM_TYPE", "User Story")
        
        if not self.org_url or not self.project or not self.pat:
            raise ValueError("Azure DevOps configuration must be set in environment variables")
        
        # Remove trailing slash if present
        self.org_url = self.org_url.rstrip('/')
        
        # Base64 encode PAT for authentication
        self.auth_header = base64.b64encode(f":{self.pat}".encode()).decode()
        
        self.base_url = f"{self.org_url}/{self.project}/_apis"
        self.api_version = "7.1"
    
    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get HTTP headers with authentication"""
        return {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": content_type
        }
    
    def _convert_markdown_to_html(self, text: str) -> str:
        """Convert markdown-style text to HTML for Azure DevOps"""
        if not text:
            return ""
        
        html_lines = []
        lines = text.split('\n')
        in_list = False
        in_table = False
        table_rows = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect table rows (lines with |)
            if '|' in line and line.count('|') >= 2:
                if not in_table:
                    in_table = True
                    table_rows = []
                
                # Parse table row
                cells = [cell.strip() for cell in line.split('|')]
                # Remove empty first/last cells if line starts/ends with |
                if cells and not cells[0]:
                    cells = cells[1:]
                if cells and not cells[-1]:
                    cells = cells[:-1]
                
                # Check if this is a separator row (all dashes)
                is_separator = all(cell.replace('-', '').strip() == '' for cell in cells if cell)
                
                if not is_separator:
                    table_rows.append(cells)
                
                i += 1
                continue
            else:
                # End of table - render it
                if in_table and table_rows:
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    
                    html_lines.append('<table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
                    
                    # First row is header
                    if table_rows:
                        html_lines.append('<thead><tr>')
                        for cell in table_rows[0]:
                            html_lines.append(f'<th style="padding: 8px; background-color: #f0f0f0; text-align: left;">{cell}</th>')
                        html_lines.append('</tr></thead>')
                    
                    # Rest are body rows
                    if len(table_rows) > 1:
                        html_lines.append('<tbody>')
                        for row in table_rows[1:]:
                            html_lines.append('<tr>')
                            for cell in row:
                                html_lines.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{cell}</td>')
                            html_lines.append('</tr>')
                        html_lines.append('</tbody>')
                    
                    html_lines.append('</table>')
                    table_rows = []
                    in_table = False
            
            if not line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<br/>')
                i += 1
                continue
            
            # Headers (lines that end with :)
            if line.endswith(':') and not line.startswith('-'):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<strong>{line}</strong><br/>')
            # Numbered lists (1., 2., etc.)
            elif line[0].isdigit() and '. ' in line[:4]:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Split number and content
                parts = line.split('. ', 1)
                if len(parts) == 2:
                    html_lines.append(f'<strong>{parts[0]}. {parts[1]}</strong><br/>')
                else:
                    html_lines.append(f'{line}<br/>')
            # Bullet points (- or *)
            elif line.startswith('-') or line.startswith('*'):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                content = line[1:].strip()
                # Check if it's a bold item (starts with **)
                if content.startswith('**') and '**' in content[2:]:
                    parts = content[2:].split('**', 1)
                    html_lines.append(f'<li><strong>{parts[0]}</strong>{parts[1] if len(parts) > 1 else ""}</li>')
                else:
                    html_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Check for bold text (**text**)
                if '**' in line:
                    line = line.replace('**', '<strong>', 1)
                    line = line.replace('**', '</strong>', 1)
                html_lines.append(f'{line}<br/>')
            
            i += 1
        
        # Close any remaining table
        if in_table and table_rows:
            html_lines.append('<table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
            if table_rows:
                html_lines.append('<thead><tr>')
                for cell in table_rows[0]:
                    html_lines.append(f'<th style="padding: 8px; background-color: #f0f0f0; text-align: left;">{cell}</th>')
                html_lines.append('</tr></thead>')
            if len(table_rows) > 1:
                html_lines.append('<tbody>')
                for row in table_rows[1:]:
                    html_lines.append('<tr>')
                    for cell in row:
                        html_lines.append(f'<td style="padding: 8px; border: 1px solid #ddd;">{cell}</td>')
                    html_lines.append('</tr>')
                html_lines.append('</tbody>')
            html_lines.append('</table>')
        
        if in_list:
            html_lines.append('</ul>')
        
        return '<div>' + ''.join(html_lines) + '</div>'
    
    def _parse_hu_content(self, hu_content: str) -> Dict[str, str]:
        """Parse HU content and extract sections for custom fields"""
        sections = {
            'como': '',
            'quiero_que': '',
            'description': '',
            'acceptance_criteria': ''
        }
        
        lines = hu_content.split('\n')
        current_section = None
        section_content = []
        skip_next_empty = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            original_line = line
            
            # Skip "Historia de Usuario" header
            if 'historia de usuario' in line_lower:
                continue
            
            # Detect section headers - more flexible detection
            # "Como" section - detect line that starts with "Como"
            if line_lower.startswith('como ') or line_lower.startswith('**como'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'como'
                section_content = []
                # Get content after "Como"
                content = line.replace('**', '').strip()
                if content.lower().startswith('como '):
                    content = content[5:].strip()  # Remove "Como "
                if content:
                    section_content.append(content)
                continue
            
            # "Quiero" section - detect line that starts with "Quiero"
            if line_lower.startswith('quiero ') or line_lower.startswith('**quiero'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                current_section = 'quiero_que'
                section_content = []
                # Get content after "Quiero"
                content = line.replace('**', '').strip()
                if content.lower().startswith('quiero '):
                    content = content[7:].strip()  # Remove "Quiero "
                if content:
                    section_content.append(content)
                continue
            
            # "Para" section - this goes into quiero_que as well
            if line_lower.startswith('para ') and current_section == 'quiero_que':
                content = line.replace('**', '').strip()
                section_content.append(content)
                continue
            
            # Major section headers that end the user story section
            if line_lower.startswith('4.') or line_lower.startswith('5.') or \
               'alcance funcional' in line_lower or 'reglas de negocio' in line_lower or \
               'criterios de aceptaci' in line_lower:
                # Save current section and switch to description
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content).strip()
                    current_section = None
                    section_content = []
                
                # Check if this is acceptance criteria
                if 'criterios de aceptaci' in line_lower or 'acceptance criteria' in line_lower:
                    current_section = 'acceptance_criteria'
                    section_content = []
                else:
                    current_section = 'description'
                    section_content = [original_line]
                continue
            
            # Add content to current section
            if current_section:
                # Skip empty lines at the start of a section
                if not line.strip() and not section_content:
                    continue
                section_content.append(original_line)
            elif line.strip():
                # If no section is active and line has content, add to description
                if current_section != 'description':
                    current_section = 'description'
                    section_content = []
                section_content.append(original_line)
        
        # Save last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content).strip()
        
        logger.info(f"Parsed sections - Como: {len(sections['como'])} chars, Quiero: {len(sections['quiero_que'])} chars, Description: {len(sections['description'])} chars, Acceptance: {len(sections['acceptance_criteria'])} chars")
        
        # If no sections found, put everything in description
        if not any(sections.values()):
            sections['description'] = hu_content
            logger.warning("No sections detected, putting all content in description")
        
        return sections
    
    async def get_work_item_types(self) -> List[str]:
        """Get list of available work item types in the project"""
        url = f"{self.base_url}/wit/workitemtypes"
        params = {"api-version": self.api_version}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"Azure DevOps API error: {response.status_code} - {response.text}")
                
                work_item_types = response.json()
                return [wit.get("name") for wit in work_item_types.get("value", [])]
        
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error getting work item types: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting work item types: {str(e)}")
    
    async def get_work_item_fields(self, work_item_type: Optional[str] = None) -> List[Dict]:
        """Get list of available fields for a work item type"""
        wit_type = work_item_type or self.work_item_type
        url = f"{self.base_url}/wit/workitemtypes/{wit_type}/fields"
        params = {"api-version": self.api_version}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"Azure DevOps API error: {response.status_code} - {response.text}")
                
                fields_data = response.json()
                fields = []
                for field in fields_data.get("value", []):
                    fields.append({
                        "name": field.get("name"),
                        "referenceName": field.get("referenceName"),
                        "type": field.get("type")
                    })
                return fields
        
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error getting work item fields: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting work item fields: {str(e)}")
    
    async def create_user_story(
        self,
        title: str,
        description: str,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        assigned_to: Optional[str] = None
    ) -> Dict:
        """Create a User Story work item in Azure DevOps"""
        
        # Extract title from HU content if not provided separately
        # Try to extract title from description (first line after "1. Título de la HU")
        if not title:
            lines = description.split('\n')
            for i, line in enumerate(lines):
                if "Título de la HU" in line and i + 1 < len(lines):
                    title = lines[i + 1].strip('-').strip()
                    break
        
        if not title:
            title = "Nueva Historia de Usuario"
        
        # Default area and iteration paths
        area_path = area_path or f"{self.project}"
        iteration_path = iteration_path or f"{self.project}"
        
        # Parse HU content into sections
        sections = self._parse_hu_content(description)
        
        # Convert each section to HTML
        como_html = self._convert_markdown_to_html(sections['como']) if sections['como'] else ""
        quiero_html = self._convert_markdown_to_html(sections['quiero_que']) if sections['quiero_que'] else ""
        description_html = self._convert_markdown_to_html(sections['description']) if sections['description'] else ""
        acceptance_html = self._convert_markdown_to_html(sections['acceptance_criteria']) if sections['acceptance_criteria'] else ""
        
        logger.info(f"HTML conversion - Como: {bool(como_html)}, Quiero: {bool(quiero_html)}, Description: {bool(description_html)}, Acceptance: {bool(acceptance_html)}")
        
        # Build work item payload with custom fields
        work_item_patches = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            },
            {
                "op": "add",
                "path": "/fields/System.WorkItemType",
                "value": self.work_item_type
            },
            {
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": area_path
            },
            {
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": iteration_path
            }
        ]
        
        # Add custom fields if they have content
        if como_html:
            work_item_patches.append({
                "op": "add",
                "path": "/fields/Custom.Como",
                "value": como_html
            })
        
        if quiero_html:
            work_item_patches.append({
                "op": "add",
                "path": "/fields/Custom.Quieroque",
                "value": quiero_html
            })
        
        if description_html:
            work_item_patches.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": description_html
            })
        
        if acceptance_html:
            work_item_patches.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                "value": acceptance_html
            })
        
        # Add tags if provided
        if tags:
            work_item_patches.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": ";".join(tags)
            })
        
        # Add assigned to if provided
        if assigned_to:
            work_item_patches.append({
                "op": "add",
                "path": "/fields/System.AssignedTo",
                "value": assigned_to
            })
        
        # Use configured work item type - need to URL encode spaces
        work_item_type_encoded = self.work_item_type.replace(" ", "%20")
        url = f"{self.base_url}/wit/workitems/${work_item_type_encoded}"
        params = {"api-version": self.api_version}
        
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Creating work item of type '{self.work_item_type}' at URL: {url}")
                response = await client.patch(
                    url,
                    headers=self._get_headers(content_type="application/json-patch+json"),
                    params=params,
                    json=work_item_patches
                )
                
                if response.status_code not in [200, 201]:
                    error_detail = response.text
                    logger.error(f"Azure DevOps API error: Status {response.status_code}, Response: {error_detail}")
                    error_msg = f"Azure DevOps API error: {response.status_code} - {error_detail}"
                    
                    # Provide helpful error messages based on status code
                    if response.status_code == 404 and "WorkItemType" in error_detail:
                        error_msg += f"\n\nSugerencia: El tipo de work item '{self.work_item_type}' no existe en este proyecto. "
                        error_msg += "Tipos comunes son: 'User Story', 'Product Backlog Item', 'Issue', 'Task', 'Bug'. "
                        error_msg += f"Puedes configurar el tipo con la variable de entorno AZURE_DEVOPS_WORK_ITEM_TYPE"
                    elif response.status_code == 401:
                        error_msg += f"\n\nSugerencia: Error de autenticación. Verifica que:"
                        error_msg += f"\n1. Tu Personal Access Token (PAT) sea válido y no haya expirado"
                        error_msg += f"\n2. El PAT tenga permisos de 'Work Items (Read, write, & manage)'"
                        error_msg += f"\n3. La variable AZURE_DEVOPS_PAT esté correctamente configurada en el archivo .env"
                    elif response.status_code == 403:
                        error_msg += f"\n\nSugerencia: No tienes permisos suficientes. Verifica que tu PAT tenga permisos de 'Work Items (Read, write, & manage)'"
                    
                    raise Exception(error_msg)
                
                work_item = response.json()
                work_item_id = work_item.get("id")
                
                # Build the URL to view the work item
                work_item_url = f"{self.org_url}/{self.project}/_workitems/edit/{work_item_id}"
                
                return {
                    "work_item_id": work_item_id,
                    "url": work_item_url,
                    "success": True
                }
        
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error creating work item: {str(e)}")
        except Exception as e:
            raise Exception(f"Error creating work item: {str(e)}")
    
    async def get_work_item(self, work_item_id: int) -> Dict:
        """Get a work item by ID"""
        url = f"{self.base_url}/wit/workitems/{work_item_id}"
        params = {"api-version": self.api_version}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                
                if response.status_code != 200:
                    raise Exception(f"Azure DevOps API error: {response.status_code} - {response.text}")
                
                return response.json()
        
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error getting work item: {str(e)}")
        except Exception as e:
            raise Exception(f"Error getting work item: {str(e)}")
