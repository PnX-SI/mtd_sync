import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { User } from '@geonature/components/auth/auth.service';
import { ConfigService } from '@geonature/services/config.service';
import { ModuleService } from '@geonature/services/module.service';
import { Observable } from 'rxjs';
import { FileData } from '../components/depobio/interfaces';

@Injectable({
  providedIn: 'root',
})
export class DemarchesSimplifieesService {
  constructor(
    private http: HttpClient,
    private config: ConfigService,
    private module: ModuleService
  ) {}

  getFile(fileNumber: string): Observable<FileData> {
    const apiUrl = `${this.config.API_ENDPOINT}/${this.config.PLUGIN_DEPOBIO.MODULE_URL}/get_file/${fileNumber}`;
    return this.http.get<FileData>(apiUrl);
  }

  createAFUrl(fileData: FileData, user: User): string {
    const params = new URLSearchParams({
      id: fileData.id,
      acquisition_framework_name: fileData.libelle,
      acquisition_framework_desc: fileData.description,
      file_id: String(fileData.number),
      state: fileData.state,
      acquisition_framework_end_date: fileData.date_fin,
      id_role: user.id_role,
      id_organism: String(user.id_organisme),
    });
    return `${this.config.URL_APPLICATION}/#/${this.module.getModule('METADATA').module_url}/af?${params.toString()}`;
  }
}
